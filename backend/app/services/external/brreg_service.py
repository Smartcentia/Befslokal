import logging
import httpx
import asyncio
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.graceful_degradation import graceful_degradation
from app.services.external_data_service import ExternalDataService

logger = logging.getLogger(__name__)


def _address_from_brreg(addr: Optional[Dict], fallback: str = "") -> str:
    """Build address string from BRREG adresse-object (adresse list + poststed)."""
    if not addr or not isinstance(addr, dict):
        return fallback
    adr_list = addr.get("adresse") or []
    poststed = addr.get("poststed") or ""
    line = (adr_list[0] if adr_list else "").strip()
    if line and poststed:
        return f"{line}, {poststed}"
    if line:
        return line
    if poststed:
        return poststed
    return fallback


def _extended_enhet_result(data: Dict[str, Any], source_label: str = "BRREG (Real Data)") -> Dict[str, Any]:
    """Build extended result from Enhetsregisteret enhet response (incl. risk fields)."""
    forretningsadresse = data.get("forretningsadresse") or {}
    postadresse = data.get("postadresse") or {}
    address = _address_from_brreg(forretningsadresse)
    if not address:
        address = _address_from_brreg(postadresse)
    if not address:
        address = "Adresse ikke tilgjengelig"

    orgform = data.get("organisasjonsform") or {}
    orgform_kode = orgform.get("kode") if isinstance(orgform, dict) else None
    orgform_beskrivelse = orgform.get("beskrivelse") if isinstance(orgform, dict) else None

    # Næringskoder
    def _naering(obj: Optional[Dict]) -> Optional[Dict]:
        if not obj or not isinstance(obj, dict):
            return None
        return {"kode": obj.get("kode"), "beskrivelse": obj.get("beskrivelse")}

    naering1 = _naering(data.get("naeringskode1"))
    naering2 = _naering(data.get("naeringskode2"))
    naering3 = _naering(data.get("naeringskode3"))

    # Institusjonell sektor
    isek = data.get("institusjonellSektorkode") or {}
    isek_kode = isek.get("kode") if isinstance(isek, dict) else None
    isek_beskrivelse = isek.get("beskrivelse") if isinstance(isek, dict) else None

    # Kapital
    kapital = data.get("kapital")
    kapital_out = None
    if kapital and isinstance(kapital, dict):
        kapital_out = {
            "belop": kapital.get("belop"),
            "antallAksjer": kapital.get("antallAksjer"),
            "valuta": kapital.get("valuta"),
            "type": kapital.get("type"),
        }

    result = {
        "id": data.get("organisasjonsnummer"),
        "name": data.get("navn"),
        "orgNr": data.get("organisasjonsnummer"),
        "email": data.get("epostadresse") or "N/A",
        "phone": data.get("telefon") or data.get("mobil") or "N/A",
        "type": "Organization",
        "address": address,
        "source": source_label,
        # Extended / risk fields
        "respons_klasse": data.get("respons_klasse"),
        "slettedato": data.get("slettedato"),
        "organisasjonsform_kode": orgform_kode,
        "organisasjonsform_beskrivelse": orgform_beskrivelse,
        "stiftelsesdato": data.get("stiftelsesdato"),
        "vedtektsdato": data.get("vedtektsdato"),
        "vedtektsfestetFormaal": data.get("vedtektsfestetFormaal"),
        "aktivitet": data.get("aktivitet"),
        "naeringskode1": naering1,
        "naeringskode2": naering2,
        "naeringskode3": naering3,
        "institusjonellSektorkode_kode": isek_kode,
        "institusjonellSektorkode_beskrivelse": isek_beskrivelse,
        "epostadresse": data.get("epostadresse"),
        "telefon": data.get("telefon"),
        "mobil": data.get("mobil"),
        "hjemmeside": data.get("hjemmeside"),
        "forretningsadresse": forretningsadresse if forretningsadresse else None,
        "postadresse": postadresse if postadresse else None,
        "konkurs": data.get("konkurs"),
        "konkursdato": data.get("konkursdato"),
        "underAvvikling": data.get("underAvvikling"),
        "underAvviklingDato": data.get("underAvviklingDato"),
        "underTvangsavviklingEllerTvangsopplosning": data.get("underTvangsavviklingEllerTvangsopplosning"),
        "tvangsavvikletPgaManglendeSlettingDato": data.get("tvangsavvikletPgaManglendeSlettingDato"),
        "tvangsopplostPgaManglendeDagligLederDato": data.get("tvangsopplostPgaManglendeDagligLederDato"),
        "tvangsopplostPgaManglendeRevisorDato": data.get("tvangsopplostPgaManglendeRevisorDato"),
        "tvangsopplostPgaManglendeRegnskapDato": data.get("tvangsopplostPgaManglendeRegnskapDato"),
        "tvangsopplostPgaMangelfulltStyreDato": data.get("tvangsopplostPgaMangelfulltStyreDato"),
        "antallAnsatte": data.get("antallAnsatte"),
        "overordnetEnhet": data.get("overordnetEnhet"),
        "kapital": kapital_out,
        "sisteInnsendteAarsregnskap": data.get("sisteInnsendteAarsregnskap"),
    }
    return result


def _slettet_enhet_result(data: Dict[str, Any]) -> Dict[str, Any]:
    """Build result for SlettetEnhet (fewer fields; no underenheter call)."""
    orgform = data.get("organisasjonsform") or {}
    orgform_kode = orgform.get("kode") if isinstance(orgform, dict) else None
    orgform_beskrivelse = orgform.get("beskrivelse") if isinstance(orgform, dict) else None
    postadresse = data.get("postadresse") or {}
    address = _address_from_brreg(postadresse, "Adresse ikke tilgjengelig (slettet enhet)")

    return {
        "id": data.get("organisasjonsnummer"),
        "name": data.get("navn"),
        "orgNr": data.get("organisasjonsnummer"),
        "email": "N/A",
        "phone": "N/A",
        "type": "Organization",
        "address": address,
        "source": "BRREG (SlettetEnhet)",
        "respons_klasse": "SlettetEnhet",
        "slettedato": data.get("slettedato"),
        "organisasjonsform_kode": orgform_kode,
        "organisasjonsform_beskrivelse": orgform_beskrivelse,
        "forretningsadresse": None,
        "postadresse": postadresse if postadresse else None,
        "konkurs": None,
        "underAvvikling": None,
        "underTvangsavviklingEllerTvangsopplosning": None,
        "antallAnsatte": None,
        "sisteInnsendteAarsregnskap": None,
    }


class BrregService:
    BASE_URL = "https://data.brreg.no/enhetsregisteret/api/enheter"
    DEFAULT_HEADERS = {
        "Accept": "application/json",
        "User-Agent": "BEFS-Eiendomsforvaltning/1.0 (https://github.com/bufetat/befs)",
    }

    @staticmethod
    async def _get_fallback_enhet(org_nr: str, db: Optional[AsyncSession] = None) -> Optional[Dict[str, Any]]:
        """Fallback function for get_enhet."""
        if not db:
            return None

        cached_data = await ExternalDataService.get_cached_api_data(
            db, source="BRREG", entity_type="party", entity_id=org_nr
        )
        if cached_data:
            cached_data["source"] = cached_data.get("source", "BRREG (Cached)") or "BRREG (Cached)"
        return cached_data

    @staticmethod
    async def get_enhet(org_nr: str, db: Optional[AsyncSession] = None) -> Optional[Dict[str, Any]]:
        """
        Fetches entity data from Brønnøysundregistrene (extended with risk fields).
        Handles SlettetEnhet explicitly: no underenheter fallback, store slettedato and respons_klasse.
        """
        if not org_nr or len(org_nr) != 9 or not org_nr.isdigit():
            logger.warning("BrregService: Invalid OrgNr format: %s", org_nr)
            return None

        url = f"{BrregService.BASE_URL}/{org_nr}"
        
        try:
            # Wrap ONLY network call in timeout
            async with httpx.AsyncClient(headers=BrregService.DEFAULT_HEADERS) as client:
                response = await asyncio.wait_for(client.get(url), timeout=10.0)

            if response.status_code == 200:
                data = response.json()
                respons_klasse = data.get("respons_klasse")

                if respons_klasse == "SlettetEnhet":
                    result = _slettet_enhet_result(data)
                else:
                    result = _extended_enhet_result(data, "BRREG (Real Data)")

                if db:
                    await ExternalDataService.save_api_data(
                        db, source="BRREG", entity_type="party", entity_id=org_nr, data=result
                    )
                return result

            if response.status_code == 404:
                url_sub = f"https://data.brreg.no/enhetsregisteret/api/underenheter/{org_nr}"
                async with httpx.AsyncClient(headers=BrregService.DEFAULT_HEADERS) as client:
                    response_sub = await asyncio.wait_for(client.get(url_sub), timeout=10.0)

                if response_sub.status_code == 200:
                    data = response_sub.json()
                    # Underenheter use beliggenhetsadresse
                    addr = data.get("beliggenhetsadresse") or {}
                    address = _address_from_brreg(addr)
                    if not address:
                        address = _address_from_brreg(data.get("postadresse") or {}, "Adresse ikke tilgjengelig")
                    data_for_extended = {**data, "forretningsadresse": data.get("beliggenhetsadresse"), "postadresse": data.get("postadresse")}
                    result = _extended_enhet_result(data_for_extended, "BRREG (SubUnit)")
                    result["address"] = address
                    result["type"] = "SubUnit"
                    if db:
                        await ExternalDataService.save_api_data(
                            db, source="BRREG", entity_type="party", entity_id=org_nr, data=result
                        )
                    return result

                logger.info("BrregService: OrgNr %s not found in main or sub-units.", org_nr)
                return None

            logger.warning("BrregService: Error %s fetching %s", response.status_code, org_nr)
            return await BrregService._get_fallback_enhet(org_nr, db)
            
        except (asyncio.TimeoutError, httpx.RequestError, Exception) as e:
            logger.warning(f"BrregService.get_enhet failed or timed out for {org_nr}: {e}. Using fallback.")
            return await BrregService._get_fallback_enhet(org_nr, db)

    ROLLER_URL = "https://data.brreg.no/enhetsregisteret/api/enheter"

    @staticmethod
    async def get_roller(org_nr: str) -> Optional[Dict[str, Any]]:
        """
        Henter roller for en enhet (daglig leder, styre, revisor, regnskapsfører).
        Åpent API, krever ikke Maskinporten.
        Returnerer forenklet struktur egnet for party.external_data["brreg_roller"].
        """
        if not org_nr or len(org_nr) != 9 or not org_nr.isdigit():
            return None
        url = f"{BrregService.ROLLER_URL}/{org_nr}/roller"
        try:
            async with httpx.AsyncClient(headers=BrregService.DEFAULT_HEADERS) as client:
                response = await client.get(url, timeout=10.0)
            if response.status_code != 200:
                return None
            data = response.json()
            rollegrupper = data.get("rollegrupper") or []
            roller_list: List[Dict[str, Any]] = []
            for rg in rollegrupper:
                rolletype = (rg.get("type") or {}).get("beskrivelse") or (rg.get("type") or {}).get("kode") or "Rolle"
                for r in rg.get("roller") or []:
                    entry: Dict[str, Any] = {"rolletype": rolletype}
                    if r.get("person"):
                        p = r["person"].get("navn") or {}
                        name = " ".join(filter(None, [p.get("fornavn"), p.get("mellomnavn"), p.get("etternavn")]))
                        entry["navn"] = name or None
                        entry["fodselsdato"] = r["person"].get("fodselsdato")
                    elif r.get("enhet"):
                        en = r["enhet"]
                        entry["navn"] = en.get("navn") if isinstance(en.get("navn"), str) else (en.get("navn") or [""])[0] if en.get("navn") else None
                        entry["organisasjonsnummer"] = en.get("organisasjonsnummer")
                        entry["type"] = "enhet"
                    if r.get("type"):
                        entry["type_kode"] = (r["type"] or {}).get("kode")
                    roller_list.append(entry)
            return {"roller": roller_list, "source": "BRREG (Roller)"}
        except Exception as e:
            logger.exception("BrregService: Exception fetching roller %s", org_nr)
            return None

    @staticmethod
    async def get_reelle_rettighetshavere(org_nr: str) -> Optional[Dict[str, Any]]:
        """
        Fetches 'Reelle Rettighetshavere' (Beneficial Owners) using Maskinporten Auth.
        """
        from app.services.auth.maskinporten_client import MaskinportenClient
        
        # Get Token
        token = await MaskinportenClient.get_access_token()
        if not token:
            logger.warning("BrregService: Failed to obtain Maskinporten token.")
            return None
            
        url = f"https://rrh.brreg.no/api/oppslag/rettighetshavere/{org_nr}" 
        
        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url, 
                    headers=headers,
                    timeout=10.0
                )
                
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                logger.warning("BrregService: RRH Error %s for %s: %s", response.status_code, org_nr, response.text)
                return None
        except Exception as e:
            logger.exception("BrregService: Exception fetching RRH %s", org_nr)
            return None

    @staticmethod
    async def get_aarsregnskap(org_nr: str) -> List[Dict[str, Any]]:
        """
        Fetches annual accounts (Årsregnskap) from Regnskapsregisteret.
        Public API – no auth required.
        Returns up to 5 years with full resultatregnskap + balanseregnskap fields.
        """
        if not org_nr or len(org_nr) != 9 or not org_nr.isdigit():
            return []

        url = f"https://data.brreg.no/regnskapsregisteret/regnskap/{org_nr}"
        try:
            async with httpx.AsyncClient(
                headers={"Accept": "application/json", "User-Agent": "BEFS-Eiendomsforvaltning/1.0"}
            ) as client:
                response = await asyncio.wait_for(client.get(url), timeout=10.0)

            if response.status_code == 404:
                logger.info("BrregService: No regnskap for %s", org_nr)
                return []
            if response.status_code != 200:
                logger.warning("BrregService: Regnskap %s for %s", response.status_code, org_nr)
                return []

            data = response.json()
            if not isinstance(data, list):
                return []

            sorted_data = sorted(
                data,
                key=lambda x: (x.get("regnskapsperiode") or {}).get("fraDato") or "",
                reverse=True,
            )

            def _n(d: dict, *keys):
                """Safe nested get, returns None if any key missing."""
                for k in keys:
                    if not isinstance(d, dict):
                        return None
                    d = d.get(k)
                return d

            results = []
            for entry in sorted_data[:5]:
                reg_period = entry.get("regnskapsperiode") or {}
                year = (reg_period.get("fraDato") or "")[:4]

                # ── Resultatregnskap ──────────────────────────────────────────
                res = entry.get("resultatregnskapResultat") or entry.get("resultatregnskap") or {}
                driftsres   = res.get("driftsresultat") or {}
                driftsinnt  = driftsres.get("driftsinntekter") or {}
                driftskost  = driftsres.get("driftskostnad") or {}
                finansres   = res.get("finansresultat") or {}
                finansinnt  = finansres.get("finansinntekt") or {}
                finanskost  = finansres.get("finanskostnad") or {}
                disponering = res.get("disponering") or {}

                operating_profit   = driftsres.get("driftsresultat")
                sum_finansinntekter = finansinnt.get("sumFinansinntekter")
                sum_finanskostnad   = finanskost.get("sumFinanskostnad")
                netto_finans        = finansres.get("nettoFinans") or finansres.get("nettFinans")
                profit_before_tax   = res.get("ordinaertResultatFoerSkattekostnad")
                if profit_before_tax is None:
                    a = operating_profit
                    b = netto_finans
                    if a is not None and b is not None:
                        profit_before_tax = a + b
                    elif a is not None:
                        profit_before_tax = a

                # ── Balanseregnskap ───────────────────────────────────────────
                eiendelene   = entry.get("eiendeler") or {}
                anlegg       = eiendelene.get("anleggsmidler") or {}
                immat        = anlegg.get("immaterielleEiendeler") or {}
                varige       = anlegg.get("varigeDriftsmidler") or {}
                finans_anl   = anlegg.get("finansielleAnleggsmidler") or {}
                omloep       = eiendelene.get("omloepsmidler") or {}
                fordringer   = omloep.get("fordringer") or {}
                invomloep    = omloep.get("investeringer") or {}

                ek_gjeld     = entry.get("egenkapitalGjeld") or {}
                egenkapital  = ek_gjeld.get("egenkapital") or {}
                innskutt_ek  = egenkapital.get("innskuttEgenkapital") or {}
                opptjent_ek  = egenkapital.get("opptjentEgenkapital") or {}
                # Large companies ("store") use "gjeldOversikt", small use "gjeld"
                gjeld        = ek_gjeld.get("gjeld") or ek_gjeld.get("gjeldOversikt") or {}
                avsetning    = gjeld.get("avsetningForpliktelser") or {}
                lang_gjeld   = gjeld.get("annenLangsiktigGjeld") or gjeld.get("langsiktigGjeld") or {}
                kortsiktig   = gjeld.get("kortsiktigGjeld") or {}

                # BRREG has a typo: "driftsloesoreInventarVerktoeuyOgLignende" / "loesoreInventarVerktoeuyOgLignende"
                driftsloesore = (
                    varige.get("loesoreInventarVerktoeuyOgLignende")
                    or varige.get("driftsloesoreInventarVerktoeuyOgLignende")
                )
                # BRREG typo in innskutt EK sum: "sumInnskuttEgenkaptial"
                sum_innskutt_ek = (
                    innskutt_ek.get("sumInnskuttEgenkaptial")
                    or innskutt_ek.get("sumInnskuttEgenkapital")
                )

                equity       = egenkapital.get("sumEgenkapital")
                sum_gjeld    = gjeld.get("sumGjeld")
                total_assets = eiendelene.get("sumEiendeler")
                sum_omloep   = omloep.get("sumOmloepsmidler")
                sum_kortsiktig = kortsiktig.get("sumKortsiktigGjeld")

                # Nøkkeltall (beregnet)
                def _safe_div(a, b):
                    return a / b if (a is not None and b is not None and b != 0) else None

                soliditet     = _safe_div(equity, total_assets) and round(equity / total_assets * 100, 1) if equity is not None and total_assets else None
                driftsmargin  = round(operating_profit / driftsinnt.get("sumDriftsinntekter") * 100, 1) if operating_profit is not None and driftsinnt.get("sumDriftsinntekter") else None
                overskuddsgrad = round(res.get("aarsresultat", 0) / driftsinnt.get("sumDriftsinntekter") * 100, 1) if res.get("aarsresultat") is not None and driftsinnt.get("sumDriftsinntekter") else None
                likviditetsgrad = round(sum_omloep / sum_kortsiktig, 2) if sum_omloep is not None and sum_kortsiktig and sum_kortsiktig > 0 else None
                gjeldsgrad    = round(sum_gjeld / equity, 2) if sum_gjeld is not None and equity and equity > 0 else None

                results.append({
                    "year": year,
                    "fra_dato": reg_period.get("fraDato"),
                    "til_dato": reg_period.get("tilDato"),
                    "currency": entry.get("valuta", "NOK"),
                    # ── Resultatregnskap
                    "salgsinntekter":       driftsinnt.get("salgsinntekter"),
                    "annen_driftsinntekt":  driftsinnt.get("annenDriftsinntekt"),
                    "revenue":              driftsinnt.get("sumDriftsinntekter"),
                    "varekostnad":          driftskost.get("varekostnad"),
                    "beholdningsendring":   driftskost.get("beholdningsendring"),
                    "loennskostnad":        driftskost.get("loennskostnad"),
                    "avskrivninger":        driftskost.get("avskrivningDriftsmidlerOgImmaterielleEiendeler"),
                    "annen_driftskostnad":  driftskost.get("annenDriftskostnad"),
                    "sum_driftskostnad":    driftskost.get("sumDriftskostnad"),
                    "operating_profit":     operating_profit,
                    "sum_finansinntekter":  sum_finansinntekter,
                    "sum_finanskostnad":    sum_finanskostnad,
                    "netto_finans":         netto_finans,
                    "profit_before_tax":    profit_before_tax,
                    "skattekostnad":        res.get("skattekostnadOrdinaertResultat"),
                    "net_income":           res.get("aarsresultat"),
                    "tilleggsutbytte":      disponering.get("tilleggsutbytte"),
                    "sum_utbytte":          disponering.get("sumUtbytte"),
                    "konsernbidrag":        disponering.get("konsernbidrag"),
                    # ── Balanseregnskap – anleggsmidler
                    "goodwill":                       immat.get("goodwill"),
                    "sum_immaterielle_eiendeler":     immat.get("sumImmaterielleEiendeler"),
                    "tomter_bygninger":               varige.get("fastEiendom"),
                    "maskiner_anlegg":                varige.get("maskinAnleggOgLignende"),
                    "driftsloesore":                  driftsloesore,
                    "sum_varige_driftsmidler":        varige.get("sumVarigeDriftsmidler"),
                    "investering_datterselskap":      finans_anl.get("aksjerInvesteringerIDatterselskap"),
                    "investering_aksjer_andeler":     finans_anl.get("investeringerIAndreforetak"),
                    "andre_finansielle_fordringer":   finans_anl.get("obligasjonerOgAndrefordringer"),
                    "sum_finansielle_anleggsmidler":  finans_anl.get("sumFinansielleAnleggsmidler"),
                    "sum_anleggsmidler":              anlegg.get("sumAnleggsmidler"),
                    # ── Balanseregnskap – omløpsmidler
                    "varer":              omloep.get("varer"),
                    "kundefordringer":    fordringer.get("kundefordringer"),
                    "andre_fordringer":   fordringer.get("andrefordringer"),
                    "konsernfordringer":  fordringer.get("konsernmellomvaerendePost"),
                    "sum_fordringer":     fordringer.get("sumFordringer"),
                    "sum_investeringer":  invomloep.get("sumInvesteringer"),
                    "sum_bankinnskudd":   omloep.get("bankInnskuddKontanterOgLignende"),
                    "sum_omloepsmidler":  sum_omloep,
                    "total_assets":       total_assets,
                    # ── Egenkapital
                    "aksjekapital":              innskutt_ek.get("aksjekapital"),
                    "overkursfond":              innskutt_ek.get("overkursfond"),
                    "sum_innskutt_egenkapital":  sum_innskutt_ek,
                    "annen_egenkapital":         opptjent_ek.get("annenEgenkapital"),
                    "sum_opptjent_egenkapital":  opptjent_ek.get("sumOpptjentEgenkapital"),
                    "equity":                    equity,
                    # ── Gjeld
                    "sum_avsetning_forpliktelser": avsetning.get("sumAvsetningerForpliktelser"),
                    "pant_gjeld_kreditt":          lang_gjeld.get("gjeldTilKredittinstitusjoner"),
                    "annen_langsiktig_gjeld":      lang_gjeld.get("annenLangsiktigGjeld"),
                    "sum_langsiktig_gjeld":        lang_gjeld.get("sumAnnenLangsiktigGjeld") or lang_gjeld.get("sumLangsiktigGjeld"),
                    "leverandorgjeld":             kortsiktig.get("leverandoergjeld"),
                    "skyldig_offentlige":          kortsiktig.get("skyldOffentligeAvgifter") or kortsiktig.get("skyldigOffentligeAvgifter"),
                    "annen_kortsiktig_gjeld":      kortsiktig.get("annenKortsiktigGjeld"),
                    "sum_kortsiktig_gjeld":        sum_kortsiktig,
                    "sum_gjeld":                   sum_gjeld,
                    "sum_ek_gjeld":                ek_gjeld.get("sumEgenkapitalGjeld"),
                    # ── Nøkkeltall
                    "soliditet":      soliditet,
                    "driftsmargin":   driftsmargin,
                    "overskuddsgrad": overskuddsgrad,
                    "likviditetsgrad": likviditetsgrad,
                    "gjeldsgrad":     gjeldsgrad,
                })

            return results

        except Exception as e:
            logger.exception("BrregService: Exception fetching Regnskap %s", org_nr)
            return []

    @staticmethod
    async def get_kunngjoringer(org_nr: str) -> List[Dict[str, Any]]:
        """
        Henter kunngjøringer/hendelser for en enhet.
        
        Siden det åpne Kunngjørings-APIet returnerer HTML eller krever spesifikke parametere vi ikke har stable,
        bruker vi Enhetsregisteret som kilde for KRITISKE hendelser (Konkurs, Tvangsoppløsning).
        
        Vi genererer "syntetiske" kunngjøringer basert på statusflaggene i Enhetsregisteret.
        Dette sikrer at RiskEngine får de kritiske signalene den trenger.
        """
        if not org_nr:
            return []

        enhet = await BrregService.get_enhet(org_nr)
        if not enhet:
            return []
            
        announcements = []
        
        # Sjekk statuser som tilsvarer alvorlige kunngjøringer
        if enhet.get("konkurs"):
            announcements.append({
                "dato": enhet.get("konkursdato", "Ukjent dato"),
                "type": "Konkursåpning",
                "beskrivelse": "Enheten er under konkursbehandling.",
                "kilde": "Enhetsregisteret (Status)"
            })
            
        if enhet.get("underTvangsavviklingEllerTvangsopplosning"):
            announcements.append({
                "dato": enhet.get("tvangsopplostPgaManglendeDagligLederDato") or 
                        enhet.get("tvangsopplostPgaMangelfulltStyreDato") or 
                        enhet.get("tvangsopplostPgaManglendeRevisorDato") or 
                        enhet.get("tvangsopplostPgaManglendeRegnskapDato") or 
                        "Ukjent dato",
                "type": "Tvangsoppløsning",
                "beskrivelse": "Enheten er under tvangsoppløsning.",
                "kilde": "Enhetsregisteret (Status)"
            })
            
        if enhet.get("underAvvikling"):
            announcements.append({
                "dato": enhet.get("underAvviklingDato", "Ukjent dato"),
                "type": "Oppbud / Avvikling",
                "beskrivelse": "Enheten er under avvikling.",
                "kilde": "Enhetsregisteret (Status)"
            })

        # TODO: Implementere diff-sjekk mot lagret historikk for å detektere "Endring av daglig leder" osv.
        # Dette krever at vi lagrer forrige state i databasen og sammenligner.
        
        return announcements

    @staticmethod
    async def get_losore(org_nr: str) -> List[Dict[str, Any]]:
        """
        Henter rettsstiftelser (heftelser/pant) fra Løsøreregisteret via Maskinporten.
        Scope: brreg:losore/tlg
        Endpoint: https://losoreregisteret.brreg.no/api/rettsstiftelser/organisasjon/{orgnr} (Eksempel/Estimert)
        
        Merk: Dokumentasjonen sier "begrenset API". Vi bruker Maskinporten-token.
        """
        if not org_nr:
            return []

        from app.services.auth.maskinporten_client import MaskinportenClient
        
        # 1. Hent token med Løsøre-scope
        token = await MaskinportenClient.get_access_token(scope="brreg:losore/tlg")
        if not token:
            logger.warning("BrregService: Could not get Maskinporten token for Løsøre.")
            return []
            
        # 2. Kall API (URL må verifiseres mot endelig dok, bruker antatt standardmønster for BRREG)
        # Se: https://brreg.github.io/docs/apidokumentasjon/losoreregisteret/rettsstiftelse/rettsstiftelse_generell/
        # URL er maskert i dok, men ofte: https://losore.brreg.no/api/v1/...
        
        # PROD URL (Eksempel basert på dok):
        url = f"https://krav.brreg.no/api/rettsstiftelser/organisasjon/{org_nr}" 
        # (NB: Dette er en kvalifisert gjetning basert på vanlig URL-struktur, da dok er vag.
        # Må oppdateres med korrekt URL fra bruker/integrasjonsguide).
        
        # Alternativ URL fra dok-søk: https://losoreregisteret.brreg.no/registerinfo/swagger-ui.html
        # La oss bruke en tryggere URL hvis mulig, eller logge URL ved 404.
        url = f"https://begrenset.brreg.no/losore/api/rettsstiftelse/organisasjon/{org_nr}" # Hypotetisk

        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=10.0)
                
            if response.status_code == 200:
                data = response.json()
                # Parse rettsstiftelser
                results = []
                for item in data:
                     # Map til vårt format
                     rettighet = item.get("rettighet", {})
                     results.append({
                         "type": rettighet.get("typeBeskrivelse", "Ukjent pant"),
                         "amount": rettighet.get("belop", 0),
                         "currency": rettighet.get("valuta", "NOK"),
                         "creditor": item.get("kreditor", {}).get("navn", "Ukjent kreditor")
                     })
                return results
            else:
                logger.warning("BrregService: Løsøre Error %s for %s", response.status_code, org_nr)
                return []
                
        except Exception as e:
            logger.exception("BrregService: Løsøre Exception %s", org_nr)
            return []

brreg_service = BrregService()
