import React, { useState, useEffect } from 'react';
import { getNS3451Codes, NS3451Code } from '../../../lib/api/ns3451Api';

interface NS3451SelectorProps {
    value?: string;
    onChange: (code: string) => void;
    className?: string;
}

export const NS3451Selector: React.FC<NS3451SelectorProps> = ({ value, onChange, className }) => {
    const [level1, setLevel1] = useState<NS3451Code[]>([]);
    const [level2, setLevel2] = useState<NS3451Code[]>([]);
    const [level3, setLevel3] = useState<NS3451Code[]>([]);

    const [selectedL1, setSelectedL1] = useState<string>('');
    const [selectedL2, setSelectedL2] = useState<string>('');
    const [selectedL3, setSelectedL3] = useState<string>('');

    // Fetch Level 1 on mount
    useEffect(() => {
        getNS3451Codes(1).then(setLevel1);
    }, []);

    // Handle L1 change
    const handleL1Change = async (e: React.ChangeEvent<HTMLSelectElement>) => {
        const code = e.target.value;
        setSelectedL1(code);
        setSelectedL2('');
        setSelectedL3('');
        setLevel2([]);
        setLevel3([]);
        onChange(code); // Allow selecting top level if needed, or clear

        if (code) {
            const children = await getNS3451Codes(2, code);
            setLevel2(children);
        }
    };

    // Handle L2 change
    const handleL2Change = async (e: React.ChangeEvent<HTMLSelectElement>) => {
        const code = e.target.value;
        setSelectedL2(code);
        setSelectedL3('');
        setLevel3([]);
        onChange(code);

        if (code) {
            const children = await getNS3451Codes(3, code);
            setLevel3(children);
        }
    };

    // Handle L3 change
    const handleL3Change = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const code = e.target.value;
        setSelectedL3(code);
        onChange(code);
    };

    return (
        <div className={`flex flex-col gap-2 ${className}`}>
            <label className="text-sm font-medium text-slate-700">NS 3451 Klassifisering</label>

            {/* Level 1 */}
            <select
                className="p-2 border rounded-md text-sm"
                value={selectedL1}
                onChange={handleL1Change}
            >
                <option value="">Velg hovedgruppe (f.eks. VVS)</option>
                {level1.map(c => (
                    <option key={c.code} value={c.code}>{c.code} {c.name}</option>
                ))}
            </select>

            {/* Level 2 */}
            {level2.length > 0 && (
                <select
                    className="p-2 border rounded-md text-sm"
                    value={selectedL2}
                    onChange={handleL2Change}
                >
                    <option value="">Velg gruppe (f.eks. Luftbehandling)</option>
                    {level2.map(c => (
                        <option key={c.code} value={c.code}>{c.code} {c.name}</option>
                    ))}
                </select>
            )}

            {/* Level 3 */}
            {level3.length > 0 && (
                <select
                    className="p-2 border rounded-md text-sm"
                    value={selectedL3}
                    onChange={handleL3Change}
                >
                    <option value="">Velg kode (f.eks. Utstyr)</option>
                    {level3.map(c => (
                        <option key={c.code} value={c.code}>{c.code} {c.name}</option>
                    ))}
                </select>
            )}

            {value && <div className="text-xs text-slate-500">Valgt kode: {value}</div>}
        </div>
    );
};
