import React, { useState } from 'react';
import { componentsApi, CreateComponentData } from '../../../lib/api/componentsApi';
import { NS3451Selector } from '../forms/NS3451Selector';

interface BuildingComponentFormProps {
    propertyId: string;
    onSuccess?: () => void;
}

export const BuildingComponentForm: React.FC<BuildingComponentFormProps> = ({ propertyId, onSuccess }) => {
    const [name, setName] = useState('');
    const [ns3451Code, setNs3451Code] = useState('');
    const [status, setStatus] = useState('active');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [message, setMessage] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);
        setMessage('');

        const payload: CreateComponentData = {
            property_id: propertyId,
            name,
            ns3451_code: ns3451Code,
            status
        };

        try {
            const result = await componentsApi.create(payload);
            if (result) {
                setMessage('Komponent opprettet!');
                setName('');
                setNs3451Code('');
                if (onSuccess) onSuccess();
            } else {
                setMessage('Feil ved opprettelse.');
            }
        } catch (error) {
            setMessage('En feil oppstod.');
            console.error(error);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="p-4 bg-white rounded shadow space-y-4 max-w-md">
            <h3 className="text-lg font-bold text-slate-800">Ny Komponent</h3>

            {message && <div className="p-2 bg-blue-50 text-blue-700 text-sm rounded">{message}</div>}

            <div>
                <label className="block text-sm font-medium text-slate-700">Navn</label>
                <input
                    type="text"
                    className="w-full p-2 border rounded mt-1"
                    value={name}
                    onChange={e => setName(e.target.value)}
                    required
                    placeholder="f.eks. Hovedvifte Øst"
                />
            </div>

            <NS3451Selector
                value={ns3451Code}
                onChange={setNs3451Code}
            />

            <div>
                <label className="block text-sm font-medium text-slate-700">Status</label>
                <select
                    className="w-full p-2 border rounded mt-1"
                    value={status}
                    onChange={e => setStatus(e.target.value)}
                >
                    <option value="active">Aktiv</option>
                    <option value="inactive">Inaktiv</option>
                    <option value="needs_repair">Trenger vedlikehold</option>
                </select>
            </div>

            <button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50"
            >
                {isSubmitting ? 'Lagrer...' : 'Opprett Komponent'}
            </button>
        </form>
    );
};
