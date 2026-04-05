// frontend/app/(auth)/register/page.tsx
"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import Link from "next/link";
import { GraduationCap, Loader2 } from "lucide-react";
import { Button }   from "@/components/ui/button";
import { Input }    from "@/components/ui/input";
import { Label }    from "@/components/ui/label";
import { Card, CardContent, CardHeader,
         CardTitle, CardDescription } from "@/components/ui/card";
import { useToast }  from "@/components/ui/use-toast";
import { api }       from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";

const schema = z.object({
  school_name:       z.string().min(3, "School name too short"),
  school_email:      z.string().email("Enter a valid email"),
  school_phone:      z.string().min(10, "Enter a valid phone number"),
  school_city:       z.string().min(2),
  school_state:      z.string().min(2),
  admin_first_name:  z.string().min(2),
  admin_last_name:   z.string().min(2),
  admin_password:    z.string().min(8, "Password must be at least 8 characters"),
});
type FormValues = z.infer<typeof schema>;
const BILLING_ENABLED = Boolean(process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID);

function RegisterForm() {
  const router       = useRouter();
  const params       = useSearchParams();
  const { toast }    = useToast();
  const setAuth      = useAuthStore((s) => s.setAuth);
  const [loading, setLoading] = useState(false);

  const tier = params.get("tier") ?? "basic";

  const { register, handleSubmit, formState: { errors } } =
    useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: FormValues) => {
    setLoading(true);
    try {
      const { data } = await api.post("/api/auth/register", values);

      setAuth(data.access_token, {
        user_id:   data.user_id,
        school_id: data.school_id,
        role:      data.role,
        full_name: data.full_name,
        email:     values.school_email,
      });

      toast({ title: "School registered!", description: "Welcome to School OS" });

      // If they came from pricing page, go back to billing
      if (BILLING_ENABLED && tier !== "basic") {
        router.push(`/pricing?tier=${tier}`);
      } else {
        router.push("/admin");
      }
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })
          ?.response?.data?.detail ?? "Registration failed";
      toast({ title: "Error", description: msg, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="border-slate-200 shadow-sm">
      <CardHeader className="pb-4">
        <CardTitle className="text-base">School details</CardTitle>
        <CardDescription className="text-xs">
          Fill in your school&apos;s information to get started
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* School info */}
          <div className="space-y-1.5">
            <Label className="text-xs">School name</Label>
            <Input className="h-9 text-sm"
              placeholder="Delhi Public School"
              {...register("school_name")} />
            {errors.school_name && (
              <p className="text-xs text-red-500">
                {errors.school_name.message}
              </p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs">School email</Label>
              <Input className="h-9 text-sm" type="email"
                placeholder="admin@school.edu.in"
                {...register("school_email")} />
              {errors.school_email && (
                <p className="text-xs text-red-500">
                  {errors.school_email.message}
                </p>
              )}
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Phone</Label>
              <Input className="h-9 text-sm" placeholder="9876543210"
                {...register("school_phone")} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs">City</Label>
              <Input className="h-9 text-sm" placeholder="New Delhi"
                {...register("school_city")} />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">State</Label>
              <Input className="h-9 text-sm" placeholder="Delhi"
                {...register("school_state")} />
            </div>
          </div>

          {/* Admin user */}
          <div className="pt-2 border-t border-slate-100">
            <p className="text-xs font-medium text-slate-600 mb-3">
              Your admin account
            </p>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label className="text-xs">First name</Label>
                <Input className="h-9 text-sm" placeholder="Rajesh"
                  {...register("admin_first_name")} />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Last name</Label>
                <Input className="h-9 text-sm" placeholder="Sharma"
                  {...register("admin_last_name")} />
              </div>
            </div>
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs">Password</Label>
            <Input className="h-9 text-sm" type="password"
              placeholder="Minimum 8 characters"
              {...register("admin_password")} />
            {errors.admin_password && (
              <p className="text-xs text-red-500">
                {errors.admin_password.message}
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
            Create school account
          </Button>

          <p className="text-center text-xs text-slate-500">
            Already have an account?{" "}
            <Link href="/login"
              className="text-blue-600 hover:underline font-medium">
              Sign in
            </Link>
          </p>
        </form>
      </CardContent>
    </Card>
  );
}

export default function RegisterPage() {
  return (
    <div className="min-h-screen bg-slate-50 flex items-center
                    justify-center p-4">
      <div className="w-full max-w-lg">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center
                          justify-center mb-3">
            <GraduationCap className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-xl font-semibold text-slate-800">
            Register your school
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            14-day free trial · No credit card required
          </p>
        </div>

        <Suspense fallback={<div className="h-[36rem]" />}>
          <RegisterForm />
        </Suspense>
      </div>
    </div>
  );
}
