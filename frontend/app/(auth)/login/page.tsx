// frontend/app/(auth)/login/page.tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { GraduationCap, Loader2 } from "lucide-react";

import { Button }   from "@/components/ui/button";
import { Input }    from "@/components/ui/input";
import { Label }    from "@/components/ui/label";
import { Card, CardContent, CardHeader,
         CardTitle, CardDescription } from "@/components/ui/card";
import { normalizeToastValue, useToast } from "@/components/ui/use-toast";

import { authApi }       from "@/lib/api";
import { useAuthStore }  from "@/lib/auth-store";

const schema = z.object({
  email:    z.string().email("Enter a valid email"),
  password: z.string().min(4, "Password too short"),
});
type FormValues = z.infer<typeof schema>;

export default function LoginPage() {
  const router    = useRouter();
  const { toast } = useToast();
  const setAuth   = useAuthStore((s) => s.setAuth);
  const [loading, setLoading] = useState(false);

  const { register, handleSubmit, formState: { errors } } =
    useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: FormValues) => {
    setLoading(true);
    try {
      const { data } = await authApi.login(values.email, values.password);

      // Save auth state
      setAuth(data.access_token, {
        user_id:   data.user_id,
        school_id: data.school_id,
        role:      data.role,
        full_name: data.full_name,
        email:     values.email,
      });

      toast({ title: "Welcome back!", description: data.full_name });

      // Redirect based on role
      const redirects: Record<string, string> = {
        admin:   "/admin",
        teacher: "/teacher",
        parent:  "/parent",
        student: "/student",
      };
      router.push(redirects[data.role] ?? "/admin");

    } catch (err: unknown) {
      const detail = (
        err as { response?: { data?: { detail?: unknown; message?: unknown } } }
      )?.response?.data?.detail;
      const fallbackMessage = (
        err as { response?: { data?: { message?: unknown } } }
      )?.response?.data?.message;
      const msg =
        normalizeToastValue(detail) ??
        normalizeToastValue(fallbackMessage) ??
        "Login failed. Check your credentials.";

      toast({
        title: "Login failed",
        description: msg,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center
                    justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center
                          justify-center mb-3">
            <GraduationCap className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-xl font-semibold text-slate-800">School OS</h1>
          <p className="text-sm text-slate-500 mt-1">
            AI-Powered School Management
          </p>
        </div>

        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="pb-4">
            <CardTitle className="text-base">Sign in</CardTitle>
            <CardDescription className="text-xs">
              Enter your school email and password
            </CardDescription>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="email" className="text-xs">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@school.edu.in"
                  className="h-9 text-sm"
                  {...register("email")}
                />
                {errors.email && (
                  <p className="text-xs text-red-500">{errors.email.message}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="password" className="text-xs">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  className="h-9 text-sm"
                  {...register("password")}
                />
                {errors.password && (
                  <p className="text-xs text-red-500">
                    {errors.password.message}
                  </p>
                )}
              </div>

              <Button
                type="submit"
                className="w-full h-9 text-sm bg-blue-600 hover:bg-blue-700"
                disabled={loading}
              >
                {loading && (
                  <Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" />
                )}
                Sign in
              </Button>
            </form>

            {/* Quick test credentials for development */}
            <div className="mt-4 p-3 bg-slate-50 rounded-lg border
                            border-slate-200">
              <p className="text-xs font-medium text-slate-600 mb-2">
                Test credentials
              </p>
              {[
                ["Admin",   "admin@dps.edu.in",   "admin123"],
                ["Teacher", "teacher1@dps.edu.in","teacher123"],
                ["Parent",  "parent1@gmail.com",  "parent123"],
              ].map(([role, email, pw]) => (
                <p key={role} className="text-xs text-slate-500 leading-5">
                  <span className="font-medium text-slate-700">{role}:</span>{" "}
                  {email} / {pw}
                </p>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
