// frontend/app/(dashboard)/teacher/copilot/page.tsx
"use client";

import { useState } from "react";
import axios from "axios";
import { api } from "@/lib/api";
import { Topbar } from "@/components/Topbar";
import { Button } from "@/components/ui/button";
import { Input }  from "@/components/ui/input";
import { Label }  from "@/components/ui/label";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select, SelectContent, SelectItem,
  SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/components/ui/use-toast";
import { Loader2, BookOpen, FileQuestion, FileText, Download } from "lucide-react";

const SUBJECTS = [
  "Mathematics","Science","English","Hindi",
  "Social Studies","Computer Science","Physics","Chemistry","Biology",
];
const GRADES = ["6","7","8","9","10","11","12"];

export default function TeacherCopilotPage() {
  const { toast }  = useToast();
  const [tab, setTab] = useState("lesson");
  const [loading, setLoading] = useState(false);
  const [result,  setResult]  = useState<Record<string, unknown> | null>(null);

  // Shared form state
  const [subject,  setSubject]  = useState("");
  const [grade,    setGrade]    = useState("");
  const [topic,    setTopic]    = useState("");
  const [duration, setDuration] = useState("45");
  const [mcqCount, setMcqCount] = useState("10");
  const [difficulty, setDifficulty] = useState("medium");
  const [wsCount,  setWsCount]  = useState("15");

  const generate = async () => {
    if (!subject || !grade || !topic) {
      toast({
        title:   "Fill all fields",
        description: "Subject, grade, and topic are required.",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      let endpoint = "";
      const body: Record<string, unknown> = { subject, grade, topic };

      if (tab === "lesson") {
        endpoint = "/api/teacher-tools/lesson-plan";
        body.duration_mins = Number(duration);
      } else if (tab === "mcq") {
        endpoint = "/api/teacher-tools/mcqs";
        body.count      = Number(mcqCount);
        body.difficulty = difficulty;
      } else {
        endpoint = "/api/teacher-tools/worksheet";
        body.question_count = Number(wsCount);
      }

      const { data } = await api.post(endpoint, body);
      setResult(data);

      toast({
        title:       "Generated successfully",
        description: `Cost: $${data.cost_usd?.toFixed(4) ?? "0.0000"}`,
      });
    } catch (error) {
      const description = axios.isAxiosError(error)
        ? typeof error.response?.data?.detail === "string"
          ? error.response.data.detail
          : error.message
        : "Something went wrong while generating content.";

      toast({
        title:   "Generation failed",
        description,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <Topbar title="AI Teacher Co-Pilot"
              subtitle="Generate lesson plans, MCQs, and worksheets instantly" />

      <div className="flex-1 overflow-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Controls panel */}
          <div className="bg-white border border-slate-200 rounded-xl p-5
                          lg:col-span-1 space-y-4">
            <p className="text-sm font-semibold text-slate-800">Configure</p>

            <Tabs value={tab} onValueChange={(v) => { setTab(v); setResult(null); }}>
              <TabsList className="w-full bg-slate-100">
                <TabsTrigger value="lesson" className="flex-1 text-xs">
                  <BookOpen className="w-3.5 h-3.5 mr-1" /> Lesson Plan
                </TabsTrigger>
                <TabsTrigger value="mcq" className="flex-1 text-xs">
                  <FileQuestion className="w-3.5 h-3.5 mr-1" /> MCQs
                </TabsTrigger>
                <TabsTrigger value="worksheet" className="flex-1 text-xs">
                  <FileText className="w-3.5 h-3.5 mr-1" /> Worksheet
                </TabsTrigger>
              </TabsList>
            </Tabs>

            {/* Common fields */}
            <div className="space-y-1.5">
              <Label className="text-xs">Subject</Label>
              <Select onValueChange={setSubject}>
                <SelectTrigger className="h-9 text-sm">
                  <SelectValue placeholder="Select subject" />
                </SelectTrigger>
                <SelectContent>
                  {SUBJECTS.map((s) => (
                    <SelectItem key={s} value={s}>{s}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs">Grade</Label>
              <Select onValueChange={setGrade}>
                <SelectTrigger className="h-9 text-sm">
                  <SelectValue placeholder="Select grade" />
                </SelectTrigger>
                <SelectContent>
                  {GRADES.map((g) => (
                    <SelectItem key={g} value={g}>Grade {g}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs">Topic</Label>
              <Input
                className="h-9 text-sm"
                placeholder="e.g. Photosynthesis"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
              />
            </div>

            {/* Tab-specific fields */}
            {tab === "lesson" && (
              <div className="space-y-1.5">
                <Label className="text-xs">Duration (minutes)</Label>
                <Select onValueChange={setDuration} defaultValue="45">
                  <SelectTrigger className="h-9 text-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {["30","40","45","60","90"].map((d) => (
                      <SelectItem key={d} value={d}>{d} min</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {tab === "mcq" && (
              <>
                <div className="space-y-1.5">
                  <Label className="text-xs">Number of questions</Label>
                  <Select onValueChange={setMcqCount} defaultValue="10">
                    <SelectTrigger className="h-9 text-sm">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {["5","10","15","20"].map((n) => (
                        <SelectItem key={n} value={n}>{n} questions</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs">Difficulty</Label>
                  <Select onValueChange={setDifficulty} defaultValue="medium">
                    <SelectTrigger className="h-9 text-sm">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="easy">Easy</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="hard">Hard</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </>
            )}

            {tab === "worksheet" && (
              <div className="space-y-1.5">
                <Label className="text-xs">Number of questions</Label>
                <Select onValueChange={setWsCount} defaultValue="15">
                  <SelectTrigger className="h-9 text-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {["10","15","20","25"].map((n) => (
                      <SelectItem key={n} value={n}>{n} questions</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            <Button
              className="w-full h-9 text-sm bg-blue-600 hover:bg-blue-700"
              onClick={generate}
              disabled={loading}
            >
              {loading
                ? <><Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" />Generating...</>
                : "Generate with AI"
              }
            </Button>

            {loading && (
              <p className="text-xs text-slate-400 text-center">
                GPT-4o is working... this takes 10–20 seconds.
              </p>
            )}
          </div>

          {/* Result panel */}
          <div className="lg:col-span-2">
            {!result && !loading && (
              <div className="h-full flex items-center justify-center
                              border border-dashed border-slate-200 rounded-xl">
                <div className="text-center">
                  <BookOpen className="w-10 h-10 text-slate-200 mx-auto mb-3" />
                  <p className="text-sm text-slate-400">
                    Configure your settings and click Generate
                  </p>
                  <p className="text-xs text-slate-300 mt-1">
                    Results appear here instantly
                  </p>
                </div>
              </div>
            )}

            {loading && (
              <div className="h-64 flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
              </div>
            )}

            {result && !loading && (
              <div className="bg-white border border-slate-200 rounded-xl
                              overflow-hidden">
                <div className="flex items-center justify-between px-5 py-3
                                border-b border-slate-100">
                  <p className="text-sm font-semibold text-slate-800 capitalize">
                    {tab === "lesson" ? "Lesson Plan" :
                     tab === "mcq"    ? "MCQ Set"     : "Worksheet"} — {topic}
                  </p>
                  <button
                    onClick={() => {
                      const blob = new Blob(
                        [JSON.stringify(result, null, 2)],
                        { type: "application/json" }
                      );
                      const url  = URL.createObjectURL(blob);
                      const a    = document.createElement("a");
                      a.href     = url;
                      a.download = `${tab}-${topic.replace(/\s+/g,"-")}.json`;
                      a.click();
                    }}
                    className="flex items-center gap-1.5 text-xs text-slate-500
                               hover:text-slate-700"
                  >
                    <Download className="w-3.5 h-3.5" />
                    Export JSON
                  </button>
                </div>

                <div className="p-5 overflow-auto max-h-[600px]">
                  <ResultDisplay result={result} tab={tab} />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Result renderer ────────────────────────────────────────────────
function ResultDisplay({
  result,
  tab,
}: {
  result: Record<string, unknown>;
  tab: string;
}) {
  if (tab === "lesson") {
    const plan = result.lesson_plan as Record<string, unknown>;
    if (!plan) return null;
    const sections = plan.sections as {
      name: string; duration_mins: number;
      activity: string; teacher_actions: string;
    }[];
    const homework = typeof plan.homework === "string" ? plan.homework : "";

    return (
      <div className="space-y-5">
        <div>
          <p className="text-base font-semibold text-slate-800">{plan.title as string}</p>
          <p className="text-xs text-slate-500 mt-0.5">
            {plan.grade as string} · {plan.subject as string} · {plan.duration_mins as number} min
          </p>
        </div>
        <div>
          <p className="text-xs font-semibold text-slate-600 mb-1">
            Learning objectives
          </p>
          <ul className="space-y-1">
            {(plan.learning_objectives as string[])?.map((o, i) => (
              <li key={i} className="text-sm text-slate-700 flex gap-2">
                <span className="text-blue-500 shrink-0">•</span>{o}
              </li>
            ))}
          </ul>
        </div>
        <div className="space-y-3">
          <p className="text-xs font-semibold text-slate-600">Lesson sections</p>
          {sections?.map((sec, i) => (
            <div key={i}
              className="border border-slate-100 rounded-lg p-3">
              <div className="flex items-center justify-between mb-1">
                <p className="text-sm font-medium text-slate-800">{sec.name}</p>
                <span className="text-xs text-slate-400">{sec.duration_mins} min</span>
              </div>
              <p className="text-xs text-slate-600 mb-1">
                <span className="font-medium">Activity:</span> {sec.activity}
              </p>
              <p className="text-xs text-slate-500">
                <span className="font-medium">Teacher:</span> {sec.teacher_actions}
              </p>
            </div>
          ))}
        </div>
        {homework && (
          <div className="p-3 bg-amber-50 rounded-lg border border-amber-100">
            <p className="text-xs font-medium text-amber-700 mb-1">Homework</p>
            <p className="text-sm text-amber-800">{homework}</p>
          </div>
        )}
      </div>
    );
  }

  if (tab === "mcq") {
    const data = result.mcqs as Record<string, unknown>;
    const questions = data?.questions as {
      number: number; question: string;
      options: Record<string,string>;
      correct_answer: string; explanation: string;
    }[];
    return (
      <div className="space-y-4">
        <p className="text-xs text-slate-500">
          {data?.topic as string} · Grade {data?.grade as string} · {data?.difficulty as string}
        </p>
        {questions?.map((q) => (
          <div key={q.number}
            className="border border-slate-100 rounded-lg p-4">
            <p className="text-sm font-medium text-slate-800 mb-3">
              {q.number}. {q.question}
            </p>
            <div className="grid grid-cols-2 gap-2 mb-3">
              {Object.entries(q.options).map(([key, val]) => (
                <div key={key}
                  className={`text-xs p-2 rounded-lg border ${
                    key === q.correct_answer
                      ? "bg-green-50 border-green-200 text-green-700 font-medium"
                      : "bg-slate-50 border-slate-200 text-slate-600"
                  }`}>
                  {key}. {val}
                </div>
              ))}
            </div>
            <p className="text-xs text-slate-500 italic">{q.explanation}</p>
          </div>
        ))}
      </div>
    );
  }

  // Worksheet
  const data = result.worksheet as Record<string, unknown>;
  const sections = data?.sections as {
    title: string; type: string; marks_each: number;
    questions: { number: number; question: string; answer: string }[];
  }[];

  return (
    <div className="space-y-5">
      <div>
        <p className="text-base font-semibold text-slate-800">{data?.title as string}</p>
        <p className="text-xs text-slate-500">{data?.instructions as string}</p>
      </div>
      {sections?.map((sec, i) => (
        <div key={i}>
          <p className="text-sm font-semibold text-slate-700 mb-2">
            {sec.title} ({sec.marks_each} mark each)
          </p>
          <div className="space-y-2">
            {sec.questions?.map((q) => (
              <div key={q.number} className="flex gap-2">
                <span className="text-xs text-slate-500 shrink-0 w-5">
                  {q.number}.
                </span>
                <div>
                  <p className="text-sm text-slate-800">{q.question}</p>
                  <p className="text-xs text-green-600 mt-0.5">
                    Ans: {q.answer}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
