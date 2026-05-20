"use client";

import { useState, useEffect } from 'react';
import { Calendar, momentLocalizer, Event } from 'react-big-calendar';
import moment from 'moment';
import 'moment/locale/nb';
import 'react-big-calendar/lib/css/react-big-calendar.css';

import { fetchAPI } from '../../../lib/api/client';

moment.locale('nb');
const localizer = momentLocalizer(moment);

interface ScheduledActivity {
    activity_id: string;
    property_id: string;
    title: string;
    description: string;
    activity_type: string;
    category: string;
    priority: string;
    next_due_date: string;
}

interface Property {
    property_id: string;
    address: string;
    city: string;
}

interface CalendarEvent extends Event {
    id: string;
    title: string;
    start: Date;
    end: Date;
    resource?: ScheduledActivity;
}

export default function HMSCalendarPage() {
    const [activities, setActivities] = useState<ScheduledActivity[]>([]);
    const [events, setEvents] = useState<CalendarEvent[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedProperty, setSelectedProperty] = useState<string>('all');
    const [selectedCategory, setSelectedCategory] = useState<string>('all');
    const [properties, setProperties] = useState<Property[]>([]);

    useEffect(() => {
        fetchProperties();
        fetchActivities();
    }, []);

    useEffect(() => {
        // Convert activities to calendar events
        const calendarEvents: CalendarEvent[] = activities
            .filter(act => {
                if (selectedProperty !== 'all' && act.property_id !== selectedProperty) return false;
                if (selectedCategory !== 'all' && act.category !== selectedCategory) return false;
                return true;
            })
            .map(activity => {
                const startDate = new Date(activity.next_due_date);
                return {
                    id: activity.activity_id,
                    title: activity.title,
                    start: startDate,
                    end: startDate,
                    resource: activity
                };
            });

        setEvents(calendarEvents);
    }, [activities, selectedProperty, selectedCategory]);

    const fetchProperties = async () => {
        try {
            const data = await fetchAPI('/properties');
            setProperties(data);
        } catch (error) {
            console.error('Failed to fetch properties:', error);
        }
    };

    const fetchActivities = async () => {
        try {
            setLoading(true);
            const data = await fetchAPI('/hms/activities/scheduled');
            setActivities(data);
        } catch (error) {
            console.error('Failed to fetch activities:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleGenerateActivities = async () => {
        if (!confirm('Vil du generere alle HMS-aktiviteter på nytt? Dette kan opprette mange nye aktiviteter.')) {
            return;
        }

        try {
            const stats = await fetchAPI('/hms/activities/generate', {
                method: 'POST',
            });
            alert(`Generert ${stats.total_activities_generated} aktiviteter for ${stats.properties_with_activities} eiendommer`);
            fetchActivities();
        } catch (error) {
            console.error('Failed to generate activities:', error);
            alert('Feil ved generering av aktiviteter');
        }
    };

    const eventStyleGetter = (event: CalendarEvent) => {
        const activity = event.resource;
        let backgroundColor = '#3174ad';

        if (activity) {
            switch (activity.priority) {
                case 'critical':
                    backgroundColor = '#dc2626'; // red
                    break;
                case 'high':
                    backgroundColor = '#ea580c'; // orange
                    break;
                case 'medium':
                    backgroundColor = '#2563eb'; // blue
                    break;
                case 'low':
                    backgroundColor = '#16a34a'; // green
                    break;
            }
        }

        return {
            style: {
                backgroundColor,
                borderRadius: '4px',
                opacity: 0.8,
                color: 'white',
                border: '0px',
                display: 'block'
            }
        };
    };

    const messages = {
        today: 'I dag',
        previous: 'Forrige',
        next: 'Neste',
        month: 'Måned',
        week: 'Uke',
        day: 'Dag',
        agenda: 'Agenda',
        date: 'Dato',
        time: 'Tid',
        event: 'Hendelse',
        noEventsInRange: 'Ingen aktiviteter i dette tidsrommet',
        showMore: (total: number) => `+ ${total} flere`
    };

    return (
        <div className="min-h-screen bg-gray-50 p-6">
            <div className="max-w-7xl mx-auto">
                <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
                    <div className="flex justify-between items-center mb-6">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900">HMS Kalender</h1>
                            <p className="text-gray-600 mt-1">
                                Planlagte HMS-aktiviteter og internkontroll
                            </p>
                        </div>
                        <button
                            onClick={handleGenerateActivities}
                            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                        >
                            Generer Aktiviteter
                        </button>
                    </div>

                    {/* Filters */}
                    <div className="flex gap-4 mb-6">
                        <div className="flex-1">
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Eiendom
                            </label>
                            <select
                                value={selectedProperty}
                                title="Velg eiendom"
                                onChange={(e) => setSelectedProperty(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="all">Alle eiendommer</option>
                                {properties.map(prop => (
                                    <option key={prop.property_id} value={prop.property_id}>
                                        {prop.address}, {prop.city}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className="flex-1">
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Kategori
                            </label>
                            <select
                                value={selectedCategory}
                                title="Velg kategori"
                                onChange={(e) => setSelectedCategory(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="all">Alle kategorier</option>
                                <option value="brann">Brannvern</option>
                                <option value="teknisk">Teknisk</option>
                                <option value="hms">HMS</option>
                                <option value="sikkerhet">Sikkerhet</option>
                                <option value="inneklima">Inneklima</option>
                            </select>
                        </div>
                    </div>

                    {/* Legend */}
                    <div className="flex gap-4 mb-4 text-sm">
                        <div className="flex items-center gap-2">
                            <div className="w-4 h-4 bg-red-600 rounded"></div>
                            <span>Kritisk</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-4 h-4 bg-orange-600 rounded"></div>
                            <span>Høy</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-4 h-4 bg-blue-600 rounded"></div>
                            <span>Medium</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-4 h-4 bg-green-600 rounded"></div>
                            <span>Lav</span>
                        </div>
                    </div>
                </div>

                {/* Calendar */}
                <div className="bg-white rounded-lg shadow-sm p-6 h-175">
                    {loading ? (
                        <div className="flex items-center justify-center h-full">
                            <div className="text-gray-500">Laster kalender...</div>
                        </div>
                    ) : (
                        <Calendar
                            localizer={localizer}
                            events={events}
                            startAccessor="start"
                            endAccessor="end"
                            style={{ height: '100%' }}
                            messages={messages}
                            eventPropGetter={eventStyleGetter}
                            popup
                            tooltipAccessor={(event: CalendarEvent) =>
                                event.resource ? `${event.resource.description}\nPrioritet: ${event.resource.priority}` : ''
                            }
                        />
                    )}
                </div>

                {/* Upcoming Activities List */}
                <div className="bg-white rounded-lg shadow-sm p-6 mt-6">
                    <h2 className="text-xl font-bold text-gray-900 mb-4">
                        Kommende aktiviteter (neste 7 dager)
                    </h2>
                    <div className="space-y-3">
                        {activities
                            .filter(act => {
                                const dueDate = new Date(act.next_due_date);
                                const now = new Date();
                                const weekFromNow = new Date();
                                weekFromNow.setDate(weekFromNow.getDate() + 7);
                                return dueDate >= now && dueDate <= weekFromNow;
                            })
                            .sort((a, b) => new Date(a.next_due_date).getTime() - new Date(b.next_due_date).getTime())
                            .map(activity => (
                                <div
                                    key={activity.activity_id}
                                    className={`border-l-4 pl-4 py-2 ${
                                        activity.priority === 'critical' ? 'border-red-600' :
                                        activity.priority === 'high' ? 'border-orange-600' :
                                        activity.priority === 'medium' ? 'border-blue-600' : 'border-green-600'
                                    }`}
                                >
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <h3 className="font-semibold text-gray-900">{activity.title}</h3>
                                            <p className="text-sm text-gray-600 mt-1">{activity.description}</p>
                                            <div className="flex gap-3 mt-2 text-xs text-gray-500">
                                                <span className="capitalize">{activity.category}</span>
                                                <span>•</span>
                                                <span className="capitalize">{activity.activity_type}</span>
                                            </div>
                                        </div>
                                        <div className="text-sm text-gray-600">
                                            {new Date(activity.next_due_date).toLocaleDateString('nb-NO', {
                                                weekday: 'short',
                                                day: 'numeric',
                                                month: 'short'
                                            })}
                                        </div>
                                    </div>
                                </div>
                            ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
