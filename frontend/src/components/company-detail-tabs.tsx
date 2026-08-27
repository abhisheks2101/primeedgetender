"use client";

import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  assignCapability,
  createExperience,
  listCapabilityCategories,
  listDocumentTypes,
  uploadDocument,
  type Company,
  type CompanyCapability,
  type CompanyDocument,
  type Experience,
  type LookupItem,
} from "@/lib/company";

const tabs = [
  "Overview",
  "Registrations",
  "Financial",
  "Capabilities",
  "Experience",
  "Machinery",
  "Personnel",
  "Locations",
  "Documents",
] as const;

interface CompanyDetailTabsProps {
  company: Company;
  experiences: Experience[];
  capabilities: CompanyCapability[];
  documents: CompanyDocument[];
  isAdmin: boolean;
}

export function CompanyDetailTabs({
  company,
  experiences,
  capabilities,
  documents,
  isAdmin,
}: CompanyDetailTabsProps) {
  const [activeTab, setActiveTab] = useState<(typeof tabs)[number]>("Overview");
  const [localExperiences, setLocalExperiences] = useState(experiences);
  const [localCapabilities, setLocalCapabilities] = useState(capabilities);
  const [localDocuments, setLocalDocuments] = useState(documents);
  const [lookupLoaded, setLookupLoaded] = useState(false);
  const [capabilityCategories, setCapabilityCategories] = useState<LookupItem[]>([]);
  const [documentTypes, setDocumentTypes] = useState<LookupItem[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [experienceForm, setExperienceForm] = useState({
    project_name: "",
    work_category: "",
    subcategory: "",
    client_department: "",
    state: "",
    district: "",
    project_status: "COMPLETED",
  });
  const [selectedCapability, setSelectedCapability] = useState("");
  const [selectedDocumentType, setSelectedDocumentType] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  const activeBadge = useMemo(
    () => (company.is_active ? "success" : "secondary") as "success" | "secondary",
    [company.is_active],
  );

  async function ensureLookups() {
    if (lookupLoaded) return;
    const [categories, types] = await Promise.all([listCapabilityCategories(), listDocumentTypes()]);
    setCapabilityCategories(categories);
    setDocumentTypes(types);
    setSelectedCapability(categories[0]?.id || "");
    setSelectedDocumentType(types[0]?.id || "");
    setLookupLoaded(true);
  }

  async function handleAddExperience() {
    const created = await createExperience(company.id, experienceForm);
    setLocalExperiences((current) => [created, ...current]);
    setMessage("Project experience added.");
  }

  async function handleAssignCapability() {
    await ensureLookups();
    if (!selectedCapability) {
      setMessage("No capability categories available.");
      return;
    }
    const created = await assignCapability(company.id, {
      capability_id: selectedCapability,
      years_of_experience: 3,
    });
    setLocalCapabilities((current) => [created, ...current]);
    setMessage("Capability assigned.");
  }

  async function handleUploadDocument() {
    try {
      await ensureLookups();
      if (!uploadFile || !selectedDocumentType) {
        setMessage("Select a document type and file before uploading.");
        return;
      }
      const created = await uploadDocument(company.id, uploadFile, selectedDocumentType, "Uploaded from company profile");
      setLocalDocuments((current) => [created, ...current]);
      setUploadFile(null);
      setMessage("Document uploaded.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Document upload failed.");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        {tabs.map((tab) => (
          <Button
            key={tab}
            variant={activeTab === tab ? "default" : "outline"}
            size="sm"
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </Button>
        ))}
      </div>

      {message ? <p className="text-sm text-emerald-700">{message}</p> : null}

      {activeTab === "Overview" ? (
        <Card>
          <CardHeader>
            <CardTitle>{company.display_name}</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="text-sm text-slate-500">Legal Name</p>
              <p>{company.legal_name}</p>
            </div>
            <div>
              <p className="text-sm text-slate-500">Status</p>
              <Badge variant={activeBadge}>{company.is_active ? "Active" : "Archived"}</Badge>
            </div>
            <div>
              <p className="text-sm text-slate-500">Location</p>
              <p>{[company.city, company.district, company.state].filter(Boolean).join(", ") || "—"}</p>
            </div>
            <div>
              <p className="text-sm text-slate-500">Contact</p>
              <p>{company.email || "—"}</p>
              <p>{company.phone || "—"}</p>
            </div>
            <div className="md:col-span-2">
              <p className="text-sm text-slate-500">Description</p>
              <p>{company.description || "No description provided."}</p>
            </div>
          </CardContent>
        </Card>
      ) : null}

      {activeTab === "Experience" ? (
        <Card>
          <CardHeader>
            <CardTitle>Project Experience</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {isAdmin ? (
              <div className="grid gap-3 md:grid-cols-2">
                <Input
                  placeholder="Project name"
                  value={experienceForm.project_name}
                  onChange={(event) => setExperienceForm((current) => ({ ...current, project_name: event.target.value }))}
                />
                <Input
                  placeholder="Work category"
                  value={experienceForm.work_category}
                  onChange={(event) => setExperienceForm((current) => ({ ...current, work_category: event.target.value }))}
                />
                <Input
                  placeholder="Subcategory"
                  value={experienceForm.subcategory}
                  onChange={(event) => setExperienceForm((current) => ({ ...current, subcategory: event.target.value }))}
                />
                <Input
                  placeholder="Client department"
                  value={experienceForm.client_department}
                  onChange={(event) =>
                    setExperienceForm((current) => ({ ...current, client_department: event.target.value }))
                  }
                />
                <Button onClick={handleAddExperience}>Add Project</Button>
              </div>
            ) : null}
            <div className="space-y-3">
              {localExperiences.map((experience) => (
                <div key={experience.id} className="rounded-lg border border-slate-100 bg-slate-50 p-4">
                  <p className="font-medium">{experience.project_name}</p>
                  <p className="text-sm text-slate-600">
                    {[experience.work_category, experience.subcategory].filter(Boolean).join(" / ") || "Uncategorized"}
                  </p>
                  <p className="text-sm text-slate-500">{experience.client_department || "No client listed"}</p>
                </div>
              ))}
              {localExperiences.length === 0 ? <p className="text-sm text-slate-500">No projects recorded yet.</p> : null}
            </div>
          </CardContent>
        </Card>
      ) : null}

      {activeTab === "Capabilities" ? (
        <Card>
          <CardHeader>
            <CardTitle>Capabilities</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {isAdmin ? (
              <div className="flex flex-wrap gap-3">
                <select
                  className="h-10 rounded-md border border-slate-200 px-3 text-sm"
                  value={selectedCapability}
                  onFocus={ensureLookups}
                  onChange={(event) => setSelectedCapability(event.target.value)}
                >
                  {capabilityCategories.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </select>
                <Button onClick={handleAssignCapability}>Assign Capability</Button>
              </div>
            ) : null}
            <div className="space-y-3">
              {localCapabilities.map((item) => (
                <div key={item.id} className="rounded-lg border border-slate-100 bg-slate-50 p-4">
                  <p className="font-medium">{item.capability.name}</p>
                  <p className="text-sm text-slate-500">{item.capability.code}</p>
                </div>
              ))}
              {localCapabilities.length === 0 ? (
                <p className="text-sm text-slate-500">No capabilities assigned yet.</p>
              ) : null}
            </div>
          </CardContent>
        </Card>
      ) : null}

      {activeTab === "Documents" ? (
        <Card>
          <CardHeader>
            <CardTitle>Documents</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {isAdmin ? (
              <div className="flex flex-wrap items-end gap-3">
                <div className="space-y-2">
                  <Label htmlFor="document-type">Document Type</Label>
                  <select
                    id="document-type"
                    className="h-10 rounded-md border border-slate-200 px-3 text-sm"
                    value={selectedDocumentType}
                    onFocus={ensureLookups}
                    onChange={(event) => setSelectedDocumentType(event.target.value)}
                  >
                    {documentTypes.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="document-file">File</Label>
                  <Input id="document-file" type="file" onChange={(event) => setUploadFile(event.target.files?.[0] || null)} />
                </div>
                <Button onClick={handleUploadDocument}>Upload Document</Button>
              </div>
            ) : null}
            <div className="space-y-3">
              {localDocuments.map((document) => (
                <div key={document.id} className="rounded-lg border border-slate-100 bg-slate-50 p-4">
                  <p className="font-medium">{document.original_filename}</p>
                  <p className="text-sm text-slate-600">{document.document_type.name}</p>
                  <Badge variant="secondary">{document.document_status}</Badge>
                </div>
              ))}
              {localDocuments.length === 0 ? <p className="text-sm text-slate-500">No documents uploaded yet.</p> : null}
            </div>
          </CardContent>
        </Card>
      ) : null}

      {["Registrations", "Financial", "Machinery", "Personnel", "Locations"].includes(activeTab) ? (
        <Card>
          <CardHeader>
            <CardTitle>{activeTab}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-600">
              Structured {activeTab.toLowerCase()} records are available through the company API. Use this tab area for
              future detailed UI expansion in later modules.
            </p>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
