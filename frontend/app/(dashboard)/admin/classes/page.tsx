"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, School2 } from "lucide-react";

import { Topbar } from "@/components/Topbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/use-toast";
import { classesApi, usersApi } from "@/lib/api";

interface Teacher {
  id: number;
  first_name: string;
  last_name: string;
}

interface ClassItem {
  id: number;
  grade: string;
  section: string;
  academic_year: string;
  class_teacher_id: number | null;
}

const schema = z.object({
  grade: z.string().min(1, "Grade is required"),
  section: z.string().min(1, "Section is required"),
  academic_year: z.string().min(4, "Academic year is required"),
  class_teacher_id: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

function toList<T>(payload: unknown): T[] {
  if (Array.isArray(payload)) return payload;
  if (!payload || typeof payload !== "object") return [];

  const candidateKeys = ["items", "results", "data"];
  for (const key of candidateKeys) {
    const value = (payload as Record<string, unknown>)[key];
    if (Array.isArray(value)) return value as T[];
  }

  return [];
}

export default function AdminClassesPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const {
    register,
    handleSubmit,
    setValue,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { academic_year: "2026-27" },
  });

  const { data: teachers, isLoading: loadingTeachers } = useQuery({
    queryKey: ["users", "teacher"],
    queryFn: () => usersApi.list({ role: "teacher" }).then((r) => toList<Teacher>(r.data)),
  });

  const { data: classes, isLoading: loadingClasses } = useQuery({
    queryKey: ["classes"],
    queryFn: () => classesApi.list().then((r) => toList<ClassItem>(r.data)),
  });

  const onSubmit = async (values: FormValues) => {
    try {
      await classesApi.create({
        grade: values.grade,
        section: values.section,
        academic_year: values.academic_year,
        class_teacher_id: values.class_teacher_id ? Number(values.class_teacher_id) : null,
      });

      toast({
        title: "Class created",
        description: `Grade ${values.grade}-${values.section} is ready for students.`,
      });
      reset({ grade: "", section: "", academic_year: values.academic_year, class_teacher_id: "" });
      queryClient.invalidateQueries({ queryKey: ["classes"] });
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Could not create class.";
      toast({ title: "Create failed", description: message, variant: "destructive" });
    }
  };

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <Topbar
        title="Classes"
        subtitle="Create each class first, then link teachers and students to it."
      />

      <div className="flex-1 space-y-6 overflow-auto p-4 sm:p-6">
        <div className="grid gap-6 lg:grid-cols-[1.1fr,0.9fr]">
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="text-sm font-semibold">Create Class</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <Label className="text-xs">Grade</Label>
                    <Input className="h-9 text-sm" placeholder="8" {...register("grade")} />
                    {errors.grade && <p className="text-xs text-red-500">{errors.grade.message}</p>}
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-xs">Section</Label>
                    <Input className="h-9 text-sm" placeholder="A" {...register("section")} />
                    {errors.section && <p className="text-xs text-red-500">{errors.section.message}</p>}
                  </div>
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <Label className="text-xs">Academic year</Label>
                    <Input className="h-9 text-sm" placeholder="2026-27" {...register("academic_year")} />
                    {errors.academic_year && (
                      <p className="text-xs text-red-500">{errors.academic_year.message}</p>
                    )}
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-xs">Class teacher</Label>
                    <select
                      className="flex h-9 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 outline-none focus:border-blue-500"
                      defaultValue=""
                      onChange={(event) => setValue("class_teacher_id", event.target.value)}
                    >
                      <option value="">Assign later</option>
                      {(teachers ?? []).map((teacher) => (
                        <option key={teacher.id} value={String(teacher.id)}>
                          {teacher.first_name} {teacher.last_name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <Button type="submit" className="h-9 bg-blue-600 hover:bg-blue-700" disabled={isSubmitting}>
                  {isSubmitting && <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />}
                  Save class
                </Button>
              </form>
            </CardContent>
          </Card>

          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="text-sm font-semibold">Setup order</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                "Create classes like 8-A, 8-B, 9-A.",
                "Create teacher accounts and assign a class teacher if you want.",
                "Create parent accounts with the email and password they will use to log in.",
                "Create students and link each student to the correct class and parent.",
              ].map((step, index) => (
                <div key={step} className="flex items-start gap-3 rounded-xl bg-slate-50 p-3">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-100 text-xs font-semibold text-blue-700">
                    {index + 1}
                  </span>
                  <p className="text-sm text-slate-600">{step}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="text-sm font-semibold">Existing Classes</CardTitle>
          </CardHeader>
          <CardContent>
            {loadingClasses || loadingTeachers ? (
              <div className="space-y-2">
                {[1, 2, 3].map((item) => (
                  <Skeleton key={item} className="h-14 w-full" />
                ))}
              </div>
            ) : (classes ?? []).length === 0 ? (
              <div className="flex min-h-40 flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50 text-center">
                <School2 className="mb-3 h-8 w-8 text-slate-300" />
                <p className="text-sm text-slate-500">No classes yet.</p>
                <p className="text-xs text-slate-400">Create your first class to begin school setup.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {(classes ?? []).map((item) => {
                  const teacher = (teachers ?? []).find((entry) => entry.id === item.class_teacher_id);

                  return (
                    <div
                      key={item.id}
                      className="flex flex-col gap-2 rounded-xl border border-slate-200 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
                    >
                      <div>
                        <p className="text-sm font-medium text-slate-800">
                          Grade {item.grade} - Section {item.section}
                        </p>
                        <p className="text-xs text-slate-500">Academic year: {item.academic_year}</p>
                      </div>
                      <p className="text-xs text-slate-500">
                        {teacher
                          ? `Class teacher: ${teacher.first_name} ${teacher.last_name}`
                          : "Class teacher: not assigned"}
                      </p>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
