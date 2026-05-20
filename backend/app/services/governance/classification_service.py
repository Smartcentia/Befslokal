from typing import List, Dict, Any, Optional
from sqlalchemy import inspect, text, select
from sqlalchemy.orm import Session
from sqlalchemy.types import JSON
from app.core.config import settings
from app.models.data_governance import DataFieldMetadata

class DataClassificationService:
    # Høysensitiv persondata (fødselsnummer, passord, tokens, etc.)
    SENSITIVE_KEYWORDS = [
        'ssn', 'fnr', 'personnummer', 'fodselsnr', 'credit', 'card',
        'password', 'hashed_password', 'token', 'secret', 'auth_code',
        'salary', 'bank', 'account_number', 'birth', 'kontonummer',
    ]

    # Finansielle data (beløp, kostnader, budsjett, transaksjoner, etc.)
    FINANCIAL_KEYWORDS = [
        # Engelsk
        'amount', 'cost', 'price', 'rent', 'budget', 'expense',
        'transaction', 'currency', 'payment', 'invoice', 'financials',
        'revenue', 'income', 'profit', 'loss', 'balance',
        # Norsk
        'belop', 'beløp', 'kostnad', 'husleie', 'budsjett', 'regnskap',
        'faktura', 'vedlikehold', 'transaksjoner', 'kontant', 'utbetaling',
        'innbetaling', 'kreditering', 'debitering',
    ]

    # Finansielle tabeller — alle kolonner klassifiseres som FINANCIAL
    FINANCIAL_TABLES = {
        'budget', 'finance_budget', 'gl_transactions', 'gl_transaction',
        'salary_costs', 'agresso_budgets', 'agresso_budget',
        'innkjop_nasjonal_summary', 'koststed_mapping', 'fixed_assets',
        'budget_items',
    }

    # Personidentifiserbar informasjon (PII)
    PII_KEYWORDS = [
        # Engelsk
        'email', 'phone', 'name', 'address', 'user', 'owner',
        'tenant', 'contact', 'mobile', 'birth_date', 'gender',
        'nationality', 'personal',
        # Norsk
        'epost', 'telefon', 'navn', 'adresse', 'bruker', 'leietaker',
        'fodselsdato', 'kjonn',
    ]

    # Interne/administrative tabeller
    INTERNAL_TABLES = {
        'users', 'user_property_association', 'sessions', 'audit_logs',
        'alembic_version', 'data_field_metadata',
    }

    @classmethod
    def classify_field(cls, table: str, column: str, path: str = "") -> str:
        full_name = f"{table}.{column}{'.' + path if path else ''}".lower()
        table_lower = table.lower()

        # Tabell-baserte regler — alle kolonner i finansielle tabeller er FINANCIAL
        if table_lower in cls.FINANCIAL_TABLES:
            return "FINANCIAL"

        # Interne tabeller
        if table_lower in cls.INTERNAL_TABLES:
            return "INTERNAL"

        # Nøkkelord-matching (sensitiv > finansiell > PII)
        if any(k in full_name for k in cls.SENSITIVE_KEYWORDS):
            return "RESTRICTED"
        if any(k in full_name for k in cls.FINANCIAL_KEYWORDS):
            return "FINANCIAL"
        if any(k in full_name for k in cls.PII_KEYWORDS):
            return "PII"

        return "PUBLIC"

    @classmethod
    async def get_catalog(cls, db: Session) -> List[Dict[str, Any]]:
        # Fetch manual overrides first
        stmt = select(DataFieldMetadata)
        result = await db.execute(stmt)
        metadata_map = {
            (m.table_name, m.column_name): m
            for m in result.scalars().all()
        }

        def _sync_inspect(sync_session):
            inspector = inspect(sync_session.connection())
            catalog = []

            for table_name in inspector.get_table_names():
                columns = inspector.get_columns(table_name)
                for col in columns:
                    col_name = col['name']
                    col_type = str(col['type'])

                    # Manual override har høyest prioritet
                    meta = metadata_map.get((table_name, col_name))
                    if meta and meta.classification_override:
                        classification = meta.classification_override
                    else:
                        classification = cls.classify_field(table_name, col_name)

                    entry = {
                        "table": table_name,
                        "column": col_name,
                        "type": col_type,
                        "classification": classification,
                        "description": meta.description if meta else None,
                        "details": None
                    }

                    # JSON-kolonner flagges separat
                    if "JSON" in col_type:
                        entry["is_json"] = True
                        if col_name in ["external_data", "amount", "data"]:
                            if not (meta and meta.classification_override):
                                entry["classification"] = "FINANCIAL" if col_name == "amount" else "PUBLIC"

                    catalog.append(entry)
            return catalog

        catalog = await db.run_sync(_sync_inspect)
        return catalog

    @classmethod
    async def update_description(cls, db: Session, table: str, column: str, description: str):
        stmt = select(DataFieldMetadata).where(
            DataFieldMetadata.table_name == table,
            DataFieldMetadata.column_name == column
        )
        result = await db.execute(stmt)
        meta = result.scalar_one_or_none()

        if meta:
            meta.description = description
        else:
            meta = DataFieldMetadata(
                table_name=table,
                column_name=column,
                description=description
            )
            db.add(meta)

        await db.commit()
        await db.refresh(meta)
        return meta

    @classmethod
    async def get_stats(cls, db: Session) -> Dict[str, Any]:
        """Returns summary statistics for the data catalog."""
        catalog = await cls.get_catalog(db)

        counts: Dict[str, int] = {}
        processed_tables: set = set()

        for entry in catalog:
            cls_name = entry["classification"]
            counts[cls_name] = counts.get(cls_name, 0) + 1
            processed_tables.add(entry["table"])

        return {
            "total_tables": len(processed_tables),
            "total_fields": len(catalog),
            "classification_counts": counts,
        }

data_classification_service = DataClassificationService()
