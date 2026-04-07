"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, Users } from "lucide-react";

import { Topbar } from "@/components/Topbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/use-toast";
import { classesApi, studentsApi, usersApi } from "@/lib/api";

interface ClassItem {
  id: number;
  grade: string;
  section: string;
  academic_year: string;
}

interface ParentUser {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
}

interface Student {
  id: number;
  class_id: number;
  parent_id: number | null;
  first_name: string;
  last_name: string;
  roll_number: string;
}

function getErrorMessage(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string" && detail.trim()) return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: string } | undefined;
    if (typeof first?.msg === "string" && first.msg.trim()) return first.msg;
  }
  return "Could not create student.";
}

const schema = z.object({
  class_id: z.string().min(1, "Select a class"),
  parent_id: z.string().optional(),
  first_name: z.string().min(2, "First name is required"),
  last_name: z.string().min(2, "Last name is required"),
  roll_number: z.string().min(1, "Roll number is required"),
  date_of_birth: z.string().optional(),
  gender: z.string().optional(),
  phone: z.string().optional(),
  address: z.string().optional(),
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

export default function AdminStudentsPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const {
    register,
    handleSubmit,
    setValue,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const { data: classes, isLoading: loadingClasses } = useQuery({
    queryKey: ["classes"],
    queryFn: () => classesApi.list().then((r) => toList<ClassItem>(r.data)),
  });

  const { data: parents, isLoading: loadingParents } = useQuery({
    queryKey: ["users", "parent"],
    queryFn: () => usersApi.list({ role: "parent" }).then((r) => toList<ParentUser>(r.data)),
  });

  const { data: students, isLoading: loadingStudents } = useQuery({
    queryKey: ["students", "active"],
    queryFn: () => studentsApi.list({ is_active: true }).then((r) => toList<Student>(r.data)),
  });

  const onSubmit = async (values: FormValues) => {
    try {
      await studentsApi.create({
        class_id: Number(values.class_id),
        parent_id: values.parent_id ? Number(values.parent_id) : null,
        first_name: values.first_name,
        last_name: values.last_name,
        roll_number: values.roll_number,
        date_of_birth: values.date_of_birth || null,
        gender: values.gender || null,
        phone: values.phone || null,
        address: values.address || null,
      });

      toast({
        title: "Student created",
        description: `${values.first_name} is now part of your school records.`,
      });
      reset();
      queryClient.invalidateQueries({ queryKey: ["students"] });
      queryClient.invalidateQueries({ queryKey: ["students", "active"] });
    } catch (err: unknown) {
      const message = getErrorMessage(err);
      toast({ title: "Create failed", description: message, variant: "destructive" });
    }
  };

  const hasClasses = (classes?.length ?? 0) > 0;

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <Topbar
        title="Students"
        subtitle="Add student records and link each child to the right class and parent."
      />

      <div className="flex-1 space-y-6 overflow-auto p-4 sm:p-6">
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="text-sm font-semibold">Create Student</CardTitle>
          </CardHeader>
          <CardContent>
            {!hasClasses && !loadingClasses ? (
              <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
                <p className="text-sm font-medium text-amber-800">Create a class first.</p>
                <p className="mt-1 text-xs text-amber-700">
                  Students need a class. Parent linking is optional in the form, but recommended for parent-facing alerts and notifications.
                </p>
              </div>
            ) : (
              <form onSubmit={handleSubmit(onSubmit)} className="grid gap-4 lg:grid-cols-2">
                <div className="space-y-1.5">
                  <Label className="text-xs">First name</Label>
                  <Input className="h-9 text-sm" {...register("first_name")} />
                  {errors.first_name && <p className="text-xs text-red-500">{errors.first_name.message}</p>}
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs">Last name</Label>
                  <Input className="h-9 text-sm" {...register("last_name")} />
                  {errors.last_name && <p className="text-xs text-red-500">{errors.last_name.message}</p>}
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs">Roll number</Label>
                  <Input className="h-9 text-sm" placeholder="2026001" {...register("roll_number")} />
                  {errors.roll_number && <p className="text-xs text-red-500">{errors.roll_number.message}</p>}
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs">Class</Label>
                  <select
                    className="flex h-9 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 outline-none focus:border-blue-500"
                    defaultValue=""
                    onChange={(event) => setValue("class_id", event.target.value)}
                  >
                    <option value="">Select class</option>
                    {(classes ?? []).map((item) => (
                      <option key={item.id} value={String(item.id)}>
                        Grade {item.grade}-{item.section} ({item.academic_year})
                      </option>
                    ))}
                  </select>
                  {errors.class_id && <p className="text-xs text-red-500">{errors.class_id.message}</p>}
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs">Parent account</Label>
                  <select
                    className="flex h-9 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 outline-none focus:border-blue-500"
                    defaultValue=""
                    onChange={(event) => setValue("parent_id", event.target.value)}
                  >
                    <option value="">Link later</option>
                    {(parents ?? []).map((parent) => (
                      <option key={parent.id} value={String(parent.id)}>
                        {parent.first_name} {parent.last_name} ({parent.email})
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs">Date of birth</Label>
                  <Input className="h-9 text-sm" type="date" {...register("date_of_birth")} />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs">Gender</Label>
                  <select
                    className="flex h-9 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 outline-none focus:border-blue-500"
                    defaultValue=""
                    {...register("gender")}
                  >
                    <option value="">Select gender</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                    <option value="prefer_not_to_say">Prefer not to say</option>
                  </select>
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs">Phone</Label>
                  <Input className="h-9 text-sm" {...register("phone")} />
                </div>
                <div className="space-y-1.5 lg:col-span-2">
                  <Label className="text-xs">Address</Label>
                  <Input className="h-9 text-sm" {...register("address")} />
                </div>
                <div className="lg:col-span-2">
                  <Button type="submit" className="h-9 bg-blue-600 hover:bg-blue-700" disabled={isSubmitting}>
                    {isSubmitting && <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />}
                    Create student
                  </Button>
                </div>
              </form>
            )}
          </CardContent>
        </Card>

        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="text-sm font-semibold">Student Records</CardTitle>
          </CardHeader>
          <CardContent>
            {loadingStudents || loadingClasses || loadingParents ? (
              <div className="space-y-2">
                {[1, 2, 3].map((item) => (
                  <Skeleton key={item} className="h-16 w-full" />
                ))}
              </div>
            ) : (students ?? []).length === 0 ? (
              <div className="flex min-h-40 flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50 text-center">
                <Users className="mb-3 h-8 w-8 text-slate-300" />
                <p className="text-sm text-slate-500">No students added yet.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {(students ?? []).map((student) => {
                  const classItem = (classes ?? []).find((item) => item.id === student.class_id);
                  const parent = (parents ?? []).find((item) => item.id === student.parent_id);

                  return (
                    <div key={student.id} className="flex flex-col gap-2 rounded-xl border border-slate-200 px-4 py-3">
                      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                        <div>
                          <p className="text-sm font-medium text-slate-800">
                            {student.first_name} {student.last_name}
                          </p>
                          <p className="text-xs text-slate-500">Roll #{student.roll_number}</p>
                        </div>
                        <p className="text-xs text-slate-500">
                          {classItem
                            ? `Class: Grade ${classItem.grade}-${classItem.section}`
                            : `Class ID: ${student.class_id}`}
                        </p>
                      </div>
                      <p className="text-xs text-slate-500">
                        {parent
                          ? `Parent: ${parent.first_name} ${parent.last_name}`
                          : "Parent: not linked yet"}
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
