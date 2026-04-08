// frontend/components/MarksEntry.tsx
"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { marksApi } from "@/lib/api";
import { useToast } from "@/components/ui/use-toast";
import { Button }   from "@/components/ui/button";
import { Input }    from "@/components/ui/input";
import { Label }    from "@/components/ui/label";
import { Loader2, TrendingDown } from "lucide-react";
import { useAuthStore } from "@/lib/auth-store";
import { emitLocalAgentLog } from "@/lib/local-agent-log";

interface Student {
  id: number; first_name: string; last_name: string;
  roll_number: string; class_id: number;
}

const schema = z.object({
  student_id: z.number().int().positive("Select a student"),
  subject:    z.string().min(1, "Select a subject"),
  exam_type:  z.string().min(1, "Select exam type"),
  exam_date:  z.string().min(1, "Select date"),
  score:      z.number().min(0).max(1000),
  max_score:  z.number().min(1).max(1000),
});
type FormValues = z.infer<typeof schema>;

const SUBJECTS  = ["Mathematics","Science","English","Hindi","Social Studies",
                   "Computer Science","Physics","Chemistry","Biology"];
const EXAM_TYPES = [
  { value: "unit_test",  label: "Unit Test"  },
  { value: "midterm",    label: "Mid Term"   },
  { value: "final",      label: "Final Exam" },
  { value: "assignment", label: "Assignment" },
  { value: "quiz",       label: "Quiz"       },
];

export function MarksEntry({ students }: { students: Student[] }) {
  const { toast } = useToast();
  const qc        = useQueryClient();
  const { user }  = useAuthStore();
  const [submitting, setSubmitting] = useState(false);
  const [lastResult, setLastResult] = useState<{
    percentage: number; student: string; subject: string;
  } | null>(null);

  const { register, handleSubmit, setValue, watch,
          reset, formState: { errors } } =
    useForm<FormValues>({ resolver: zodResolver(schema) });

  const score    = watch("score");
  const maxScore = watch("max_score");
  const pct =
    typeof score === "number" &&
    !Number.isNaN(score) &&
    typeof maxScore === "number" &&
    !Number.isNaN(maxScore) &&
    maxScore > 0
      ? Math.round((score / maxScore) * 100)
      : null;

  const onSubmit = async (values: FormValues) => {
    setSubmitting(true);
    try {
      const student = students.find((s) => s.id === values.student_id);
      if (!student) {
        throw new Error("Student not found");
      }

      await marksApi.enter({
        ...values,
        class_id: student.class_id,
      });
      const percentage =
        values.max_score > 0 ? Math.round((values.score / values.max_score) * 100) : 0;

      setLastResult({
        percentage,
        student:    `${student.first_name} ${student.last_name}`,
        subject: values.subject,
      });

      if (user?.school_id) {
        const riskLevel = percentage <= 20 ? "HIGH" : percentage < 50 ? "MEDIUM" : "LOW";
        const riskNote =
          riskLevel === "HIGH"
            ? "Score is critically low. Immediate parent intervention recommended."
            : riskLevel === "MEDIUM"
            ? "Score is below expected range. Close monitoring advised."
            : "Performance acceptable.";

        emitLocalAgentLog(user.school_id, {
          agent_name: "academic_agent",
          trigger: "marks_entered",
          action_taken: `${riskLevel} risk: ${student.first_name} scored ${values.score}/${values.max_score} in ${values.subject}. ${riskNote}`,
          outcome: "success",
          duration_ms: null,
          cost_usd: 0,
        });

        if (riskLevel === "HIGH") {
          emitLocalAgentLog(user.school_id, {
            agent_name: "teacher_agent",
            trigger: "parent_alert_queued",
            action_taken:
              `HIGH risk alert queued for parent: ${student.first_name} scored ${values.score}/${values.max_score} in ${values.subject}.`,
            outcome: "success",
            duration_ms: null,
            cost_usd: 0,
          });

          toast({
            title: "High-risk alert triggered",
            description:
              `Parent alert queued for ${student.first_name} (${values.score}/${values.max_score}).`,
          });
        }
      }

      toast({
        title:       "Marks saved",
        description: `${student.first_name} - ${values.subject}: ${percentage}%`,
      });

      qc.invalidateQueries({ queryKey: ["marks"] });
      reset();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
      const message =
        typeof detail === "string" && detail.trim()
          ? detail
          : Array.isArray(detail) && typeof (detail[0] as { msg?: string } | undefined)?.msg === "string"
          ? ((detail[0] as { msg?: string }).msg as string)
          : "Failed to save marks.";
      toast({
        title:   "Failed to save",
        description: message,
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Form */}
      <div className="bg-white border border-slate-200 rounded-xl p-5">
        <p className="text-sm font-semibold text-slate-800 mb-4">
          Enter Marks
        </p>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Student select */}
          <div className="space-y-1.5">
            <Label className="text-xs">Student</Label>
            <select
              className="flex h-9 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 outline-none focus:border-blue-500"
              defaultValue=""
              onChange={(event) => setValue("student_id", Number(event.target.value))}
            >
              <option value="" disabled>Select student</option>
                {students.map((s) => (
                <option key={s.id} value={String(s.id)}>
                    {s.first_name} {s.last_name} (Roll #{s.roll_number})
                </option>
                ))}
            </select>
            {errors.student_id && (
              <p className="text-xs text-red-500">
                {errors.student_id.message}
              </p>
            )}
          </div>

          {/* Subject + exam type */}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label className="text-xs">Subject</Label>
              <select
                className="flex h-9 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 outline-none focus:border-blue-500"
                defaultValue=""
                onChange={(event) => setValue("subject", event.target.value)}
              >
                <option value="" disabled>Subject</option>
                  {SUBJECTS.map((s) => (
                  <option key={s} value={s}>{s}</option>
                  ))}
              </select>
              {errors.subject && (
                <p className="text-xs text-red-500">{errors.subject.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs">Exam type</Label>
              <select
                className="flex h-9 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 outline-none focus:border-blue-500"
                defaultValue=""
                onChange={(event) => setValue("exam_type", event.target.value)}
              >
                <option value="" disabled>Type</option>
                  {EXAM_TYPES.map(({ value, label }) => (
                  <option key={value} value={value}>{label}</option>
                  ))}
              </select>
              {errors.exam_type && (
                <p className="text-xs text-red-500">{errors.exam_type.message}</p>
              )}
            </div>
          </div>

          {/* Score + max score */}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label className="text-xs">Score</Label>
              <Input
                type="number"
                className="h-9 text-sm"
                placeholder="45"
                {...register("score", { valueAsNumber: true })}
              />
              {errors.score && (
                <p className="text-xs text-red-500">{errors.score.message}</p>
              )}
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Out of</Label>
              <Input
                type="number"
                className="h-9 text-sm"
                placeholder="100"
                {...register("max_score", { valueAsNumber: true })}
              />
              {errors.max_score && (
                <p className="text-xs text-red-500">{errors.max_score.message}</p>
              )}
            </div>
          </div>

          {/* Live percentage preview */}
          {pct !== null && (
            <div className={`flex flex-wrap items-center gap-2 p-2.5 rounded-lg text-sm
                            font-medium
                            ${pct < 40
                              ? "bg-red-50 text-red-700"
                              : pct < 60
                              ? "bg-amber-50 text-amber-700"
                              : "bg-green-50 text-green-700"
                            }`}>
              {pct < 40 && <TrendingDown className="w-4 h-4" />}
              {pct}% — {pct < 40 ? "Fail" : pct < 60 ? "Below average"
                        : pct < 80 ? "Average" : "Good"}
              {pct < 50 && (
                <span className="text-xs font-normal opacity-70 sm:ml-auto">
                  Agent will check this
                </span>
              )}
            </div>
          )}

          {/* Date */}
          <div className="space-y-1.5">
            <Label className="text-xs">Exam date</Label>
            <Input
              type="date"
              className="h-9 text-sm"
              defaultValue={`${new Date().getFullYear()}-${String(new Date().getMonth() + 1).padStart(2, "0")}-${String(new Date().getDate()).padStart(2, "0")}`}
              {...register("exam_date")}
            />
            {errors.exam_date && (
              <p className="text-xs text-red-500">{errors.exam_date.message}</p>
            )}
          </div>

          <Button
            type="submit"
            className="w-full h-9 text-sm bg-blue-600 hover:bg-blue-700"
            disabled={submitting}
          >
            {submitting && (
              <Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" />
            )}
            Save marks
          </Button>
        </form>
      </div>

      {/* Right panel — result + tip */}
      <div className="space-y-4">
        {lastResult ? (
          <div className="bg-white border border-slate-200 rounded-xl p-5">
            <p className="text-xs text-slate-500 mb-3">Last saved</p>
            <p className="text-sm font-medium text-slate-800">
              {lastResult.student}
            </p>
            <p className="text-xs text-slate-500 mb-3">{lastResult.subject}</p>
            <p className={`text-3xl font-bold ${
              lastResult.percentage < 40 ? "text-red-600"
              : lastResult.percentage < 60 ? "text-amber-600"
              : "text-green-600"
            }`}>
              {lastResult.percentage}%
            </p>

            {lastResult.percentage < 50 && (
              <div className="mt-3 p-3 bg-blue-50 rounded-lg border
                              border-blue-100">
                <p className="text-xs text-blue-700 font-medium">
                  AI Agent triggered
                </p>
                <p className="text-xs text-blue-600 mt-0.5">
                  {lastResult.percentage <= 20
                    ? "Critical risk detected. Parent alert has been queued."
                    : "Academic Agent is monitoring this score. Parent alert is sent only for HIGH risk."}
                </p>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-5
                          flex flex-col items-center justify-center min-h-40">
            <p className="text-sm text-slate-400 text-center">
              Enter marks on the left. The result and AI agent status will
              appear here.
            </p>
          </div>
        )}

        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <p className="text-xs font-medium text-slate-700 mb-2">
            How the AI works
          </p>
          <div className="space-y-2">
            {[
              "You save marks here",
              "An event fires to the AI layer instantly",
              "Academic Agent analyses the student's trend",
              "If score dropped 15%+ → parent WhatsApp alert sent",
              "Agent logs every action — visible in Admin panel",
            ].map((step, i) => (
              <div key={i} className="flex items-start gap-2">
                <span className="w-4 h-4 rounded-full bg-blue-100 text-blue-600
                                 text-xs flex items-center justify-center
                                 shrink-0 mt-0.5 font-medium">
                  {i + 1}
                </span>
                <p className="text-xs text-slate-500">{step}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
