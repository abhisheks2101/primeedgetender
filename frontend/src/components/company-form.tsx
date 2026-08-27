"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createCompany, updateCompany, type Company } from "@/lib/company";

interface CompanyFormProps {
  initial?: Company;
}

export function CompanyForm({ initial }: CompanyFormProps) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [form, setForm] = useState({
    legal_name: initial?.legal_name || "",
    display_name: initial?.display_name || "",
    legal_entity_type: initial?.legal_entity_type || "",
    registration_number: initial?.registration_number || "",
    city: initial?.city || "",
    district: initial?.district || "",
    state: initial?.state || "",
    email: initial?.email || "",
    phone: initial?.phone || "",
    description: initial?.description || "",
  });

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      const payload = {
        ...form,
        legal_entity_type: form.legal_entity_type || null,
        registration_number: form.registration_number || null,
        city: form.city || null,
        district: form.district || null,
        state: form.state || null,
        email: form.email || null,
        phone: form.phone || null,
        description: form.description || null,
      };
      const company = initial
        ? await updateCompany(initial.id, payload)
        : await createCompany(payload);
      router.push(`/app/companies/${company.id}`);
      router.refresh();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to save company.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{initial ? "Edit Company" : "Create Company"}</CardTitle>
      </CardHeader>
      <CardContent>
        <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit}>
          {[
            ["legal_name", "Legal Name"],
            ["display_name", "Display Name"],
            ["legal_entity_type", "Entity Type"],
            ["registration_number", "Registration Number"],
            ["city", "City"],
            ["district", "District"],
            ["state", "State"],
            ["email", "Email"],
            ["phone", "Phone"],
          ].map(([key, label]) => (
            <div key={key} className="space-y-2">
              <Label htmlFor={key}>{label}</Label>
              <Input
                id={key}
                value={form[key as keyof typeof form]}
                onChange={(event) => setForm((current) => ({ ...current, [key]: event.target.value }))}
                required={key === "legal_name" || key === "display_name"}
              />
            </div>
          ))}
          <div className="space-y-2 md:col-span-2">
            <Label htmlFor="description">Description</Label>
            <Input
              id="description"
              value={form.description}
              onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
            />
          </div>
          {error ? <p className="md:col-span-2 text-sm text-red-600">{error}</p> : null}
          <div className="md:col-span-2">
            <Button type="submit" disabled={isLoading}>
              {isLoading ? "Saving..." : initial ? "Save Changes" : "Create Company"}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
