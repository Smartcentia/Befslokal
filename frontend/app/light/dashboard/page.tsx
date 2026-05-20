import React from 'react';
import { Card } from "@/components/light/Card";
import { Button } from "@/components/light/Button";
import { ActivityItem } from "@/components/light/ActivityItem";
import { InputGroup } from "@/components/light/InputGroup";
import { StatRing } from "@/components/light/StatRing";
import { Smile, Zap, Coffee, Moon } from "lucide-react";

export default function LightDashboard() {
    return (
        <div className="space-y-8">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <div className="flex items-center gap-2 text-[#FF8BA7] font-bold text-xs tracking-widest uppercase mb-2">
                        At Home / Daily / Light
                    </div>
                    <h1 className="text-4xl md:text-5xl font-serif text-gray-900 leading-tight">
                        Training that fits your day.
                    </h1>
                    <p className="text-gray-500 mt-2 max-w-xl">
                        Track gentle movement, calm energy, and small wins. A daily program you can finish in under 30 minutes.
                    </p>
                </div>

                {/* Date Pill */}
                <div className="bg-white/60 backdrop-blur-md px-6 py-3 rounded-2xl border border-white flex flex-col items-center shadow-sm">
                    <span className="text-xs text-gray-400 font-medium uppercase">Today</span>
                    <span className="text-gray-900 font-bold">mandag 16. februar</span>
                    <div className="mt-1 text-[10px] text-[#FF8BA7] font-bold">
                        0 done • 0 min • 0 reps • 0 cal
                    </div>
                </div>
            </div>

            {/* Quick Check-in Bar */}
            <div className="bg-[#1F2937] text-white p-4 rounded-2xl flex justify-between items-center shadow-lg shadow-gray-900/10">
                <span className="text-sm font-medium px-2">
                    Quick check-in: Add a light activity to keep your daily streak.
                </span>
                <button className="text-xs bg-white/10 hover:bg-white/20 px-4 py-1.5 rounded-full transition-colors">
                    Dismiss
                </button>
            </div>

            {/* Main Grid Layout */}
            <div className="grid grid-cols-1 md:grid-cols-12 gap-6">

                {/* Left Column: Daily Program (Timeline) */}
                <div className="md:col-span-4 space-y-6">
                    <Card className="h-full">
                        <div className="flex justify-between items-center mb-8">
                            <h3 className="font-bold text-lg text-gray-900">Daily light program</h3>
                            <span className="px-2 py-1 bg-gray-100 text-xs font-bold rounded-md">Home</span>
                        </div>

                        <div className="space-y-2">
                            <ActivityItem
                                time="5 min"
                                title="Wake-up mobility"
                                description="Neck rolls, shoulder circles, ankle rotations."
                                color="text-blue-500"
                            />
                            <ActivityItem
                                time="8-10 min"
                                title="Gentle flow"
                                description="Cat-cow, child's pose, hip openers."
                                color="text-indigo-500"
                            />
                            <ActivityItem
                                time="5-8 min"
                                title="Light strength"
                                description="Wall push-ups, bodyweight squats, standing marches."
                                color="text-purple-500"
                            />
                            <ActivityItem
                                time="3-5 min"
                                title="Cool down"
                                description="Slow breathing, forward fold, seated twist."
                                color="text-pink-500"
                                isLast
                            />
                        </div>
                    </Card>
                </div>

                {/* Middle Column: Focus & Suggestions */}
                <div className="md:col-span-4 space-y-6 flex flex-col">
                    <Card className="flex-1">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="font-bold text-lg text-gray-900">Daily focus</h3>
                            <span className="bg-gray-900 text-white text-[10px] px-2 py-0.5 rounded-full">Core</span>
                        </div>

                        <div className="flex items-center justify-between mb-8">
                            <StatRing percentage={0} label="Today" />
                            <div className="space-y-3 text-right">
                                <div>
                                    <div className="text-xs text-gray-400 uppercase">Goal minutes</div>
                                    <div className="text-xl font-bold text-gray-900">20</div>
                                </div>
                                <div>
                                    <div className="text-xs text-gray-400 uppercase">Goal reps</div>
                                    <div className="text-xl font-bold text-gray-900">60</div>
                                </div>
                            </div>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="text-xs font-bold text-gray-400 uppercase mb-1 block">Intensity</label>
                                <div className="w-full bg-gray-100 rounded-full h-2">
                                    <div className="bg-[#C4B5FD] h-2 rounded-full w-[30%]"></div>
                                </div>
                                <div className="text-xs text-gray-500 mt-1">Light</div>
                            </div>

                            <div>
                                <label className="text-xs font-bold text-gray-400 uppercase mb-1 block">Energy (1-5)</label>
                                <input type="range" min="1" max="5" defaultValue="3" className="w-full accent-[#FF8BA7]" />
                            </div>
                        </div>
                    </Card>

                    {/* Suggestion Card */}
                    <Card gradient className="bg-gradient-to-br from-[#E0F2FE] to-white border-blue-100">
                        <div className="flex justify-between items-start">
                            <div>
                                <div className="text-[10px] font-bold text-blue-500 uppercase mb-1">Today Suggestion</div>
                                <h4 className="font-bold text-gray-900 mb-1">Wall push-ups</h4>
                                <div className="text-sm text-gray-600">4 min • 20 reps • 25 cal</div>
                            </div>
                            <Button size="sm" className="bg-blue-500 shadow-blue-200">Add</Button>
                        </div>
                    </Card>
                </div>

                {/* Right Column: Activity Log */}
                <div className="md:col-span-4 space-y-6">
                    <Card className="h-full">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="font-bold text-lg text-gray-900">Your activity log</h3>
                            <span className="bg-black text-white p-1 rounded-full"><Zap size={14} /></span>
                        </div>

                        <form className="space-y-4 mb-8">
                            <div className="grid grid-cols-2 gap-4">
                                <InputGroup label="Activity" placeholder="Swimming, yoga..." />
                                <InputGroup label="Minutes" placeholder="15" type="number" />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <InputGroup label="Reps" placeholder="10" type="number" />
                                <InputGroup label="Calories" placeholder="80" type="number" />
                            </div>
                            <InputGroup label="Notes (optional)" placeholder="Energy level, how it felt..." />

                            <Button className="w-full mt-2">Add activity</Button>
                        </form>

                        <div className="flex gap-2 mb-6">
                            <span className="px-3 py-1 bg-gray-50 border border-gray-100 rounded-lg text-xs font-medium text-gray-600">Mobility 5m</span>
                            <span className="px-3 py-1 bg-gray-50 border border-gray-100 rounded-lg text-xs font-medium text-gray-600">Yoga 12m</span>
                            <span className="px-3 py-1 bg-gray-50 border border-gray-100 rounded-lg text-xs font-medium text-gray-600">Walk 15m</span>
                        </div>

                        {/* Previous entries */}
                        <div className="space-y-4">
                            <div className="flex justify-between items-start p-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors cursor-pointer group">
                                <div className="flex gap-3">
                                    <div className="bg-white p-2 rounded-lg text-gray-400 group-hover:text-[#FF8BA7] transition-colors"><div className="w-4 h-4 border-2 border-current rounded-sm" /></div>
                                    <div>
                                        <div className="font-bold text-sm text-gray-900">Wall push-ups</div>
                                        <div className="text-xs text-gray-500">4 min • 20 reps • 25 cal</div>
                                        <div className="text-[10px] text-gray-400 mt-0.5">Smooth tempo</div>
                                    </div>
                                </div>
                                <button className="text-[10px] text-gray-400 hover:text-red-400">Remove</button>
                            </div>

                            <div className="flex justify-between items-start p-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors cursor-pointer group">
                                <div className="flex gap-3">
                                    <div className="bg-white p-2 rounded-lg text-gray-400 group-hover:text-blue-400 transition-colors"><div className="w-4 h-4 border-2 border-current rounded-sm" /></div>
                                    <div>
                                        <div className="font-bold text-sm text-gray-900">Løping</div>
                                        <div className="text-xs text-gray-500">30 min • 5 km • 300 cal</div>
                                        <div className="text-[10px] text-gray-400 mt-0.5">Mild</div>
                                    </div>
                                </div>
                                <button className="text-[10px] text-gray-400 hover:text-red-400">Remove</button>
                            </div>
                        </div>
                    </Card>
                </div>
            </div>

            {/* Bottom Section: Badges & History */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-12">
                <Card>
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="font-bold text-gray-900">Last 7 days</h3>
                        <span className="text-[10px] bg-gray-900 text-white px-2 py-0.5 rounded-full">Overview</span>
                    </div>
                    <div className="flex justify-between text-center">
                        {['man', 'tir', 'ons', 'tor', 'fre', 'lør', 'søn'].map((day) => (
                            <div key={day} className="flex flex-col items-center gap-2 group cursor-pointer">
                                <div className="text-xs text-gray-400 uppercase font-medium">{day}</div>
                                <div className="w-8 h-20 bg-gray-100 rounded-full relative overflow-hidden group-hover:bg-gray-200 transition-colors">
                                    <div className="absolute bottom-0 w-full bg-[#FF8BA7] h-[40%] rounded-b-full opacity-80" />
                                </div>
                                <div className="text-xs font-bold text-gray-900">2</div>
                            </div>
                        ))}
                    </div>
                </Card>

                <Card>
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="font-bold text-gray-900">Badges</h3>
                        <span className="text-[10px] bg-gray-900 text-white px-2 py-0.5 rounded-full">Streak</span>
                    </div>
                    <div className="space-y-4">
                        <div className="flex justify-between items-center p-3 border border-gray-100 rounded-xl">
                            <span className="text-sm font-medium text-gray-600">3-day streak</span>
                            <span className="text-xs text-gray-400">7 days to go</span>
                        </div>
                        <div className="flex justify-between items-center p-3 border border-gray-100 rounded-xl">
                            <span className="text-sm font-medium text-gray-600">14-day streak</span>
                            <span className="text-xs text-gray-400">10 days to go</span>
                        </div>
                    </div>
                </Card>
            </div>

        </div>
    );
}
