"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, UserCheck } from "lucide-react";

import { Topbar } from "@/components/Topbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/use-toast";
import { usersApi } from "@/lib/api";

interface Teacher {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string | null;
}

const schema = z.object({
  first_name: z.string().min(2, "First name is required"),
  last_name: z.string().min(2, "Last name is required"),
  email: z.string().email("Enter a valid email"),
  phone: z.string().optional(),
  password: z.string().min(8, "Password must be at least 8 characters"),
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

export default function AdminTeachersPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const { data: teachers, isLoading } = useQuery({
    queryKey: ["users", "teacher"],
    queryFn: () => usersApi.list({ role: "teacher" }).then((r) => toList<Teacher>(r.data)),
  });

  const onSubmit = async (values: FormValues) => {
    try {
      await usersApi.create({
        role: "teacher",
        first_name: values.first_name,
        last_name: values.last_name,
        email: values.email,
        phone: values.phone || null,
        password: values.password,
        language: "en",
      });

      toast({
        title: "Teacher created",
        description: `${values.first_name} can now log in with the email and password you set.`,
      });
      reset();
      queryClient.invalidateQueries({ queryKey: ["users", "teacher"] });
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Could not create teacher.";
      toast({ title: "Create failed", description: message, variant: "destructive" });
    }
  };

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <Topbar
        title="Teachers"
        subtitle="Create a login account for each teacher in your school."
      />

      <div className="flex-1 space-y-6 overflow-auto p-4 sm:p-6">
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="text-sm font-semibold">Create Teacher</CardTitle>
          </CardHeader>
          <CardContent>
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
                <Label className="text-xs">Email</Label>
                <Input className="h-9 text-sm" type="email" {...register("email")} />
                {errors.email && <p className="text-xs text-red-500">{errors.email.message}</p>}
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Phone</Label>
                <Input className="h-9 text-sm" {...register("phone")} />
              </div>
              <div className="space-y-1.5 lg:col-span-2">
                <Label className="text-xs">Password</Label>
                <Input className="h-9 text-sm" type="password" {...register("password")} />
                {errors.password && <p className="text-xs text-red-500">{errors.password.message}</p>}
              </div>
              <div className="lg:col-span-2">
                <Button type="submit" className="h-9 bg-blue-600 hover:bg-blue-700" disabled={isSubmitting}>
                  {isSubmitting && <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />}
                  Create teacher
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="text-sm font-semibold">Teacher Accounts</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-2">
                {[1, 2, 3].map((item) => (
                  <Skeleton key={item} className="h-14 w-full" />
                ))}
              </div>
            ) : (teachers ?? []).length === 0 ? (
              <div className="flex min-h-40 flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50 text-center">
                <UserCheck className="mb-3 h-8 w-8 text-slate-300" />
                <p className="text-sm text-slate-500">No teachers added yet.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {(teachers ?? []).map((teacher) => (
                  <div
                    key={teacher.id}
                    className="flex flex-col gap-1 rounded-xl border border-slate-200 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div>
                      <p className="text-sm font-medium text-slate-800">
                        {teacher.first_name} {teacher.last_name}
                      </p>
                      <p className="text-xs text-slate-500">{teacher.email}</p>
                    </div>
                    <p className="text-xs text-slate-500">{teacher.phone || "No phone added"}</p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
