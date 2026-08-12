"use client";

import { useState, type FormEvent } from "react";
import { useApiQuery } from "@/lib/use-api-query";
import { apiClient, ApiError } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

interface UserRow {
  id: string;
  username: string;
  full_name: string;
  email: string;
  is_active: boolean;
  roles: string[];
}

interface RoleRow {
  id: string;
  name: string;
  description: string | null;
  is_system_role: boolean;
  permission_codes: string[];
}

interface PermissionRow {
  id: string;
  code: string;
  module: string;
  action: string;
  description: string | null;
}

interface OrganizationRow {
  id: string;
  name: string;
  code: string;
  org_type: string;
}

function NewUserForm({ onCreated }: { onCreated: () => void }) {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await apiClient.post("/users", { username, email, full_name: fullName, password });
      setUsername("");
      setEmail("");
      setFullName("");
      setPassword("");
      onCreated();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create user");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3 border-b border-border pb-4">
      <div>
        <label className="mb-1 block text-sm font-medium" htmlFor="newUsername">
          Username
        </label>
        <Input id="newUsername" value={username} onChange={(e) => setUsername(e.target.value)} required />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium" htmlFor="newEmail">
          Email
        </label>
        <Input id="newEmail" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium" htmlFor="newFullName">
          Full Name
        </label>
        <Input id="newFullName" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium" htmlFor="newPassword">
          Password
        </label>
        <Input
          id="newPassword"
          type="password"
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </div>
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Creating..." : "Create User"}
      </Button>
      {error && <p className="w-full text-sm text-destructive">{error}</p>}
    </form>
  );
}

function NewRoleForm({ onCreated }: { onCreated: () => void }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await apiClient.post("/roles", { name, description: description || undefined });
      setName("");
      setDescription("");
      onCreated();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create role");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3 border-b border-border pb-4">
      <div>
        <label className="mb-1 block text-sm font-medium" htmlFor="newRoleName">
          Name
        </label>
        <Input id="newRoleName" value={name} onChange={(e) => setName(e.target.value)} required />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium" htmlFor="newRoleDescription">
          Description
        </label>
        <Input id="newRoleDescription" value={description} onChange={(e) => setDescription(e.target.value)} />
      </div>
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Creating..." : "Create Role"}
      </Button>
      {error && <p className="w-full text-sm text-destructive">{error}</p>}
    </form>
  );
}

function RolePermissionsEditor({
  role,
  allPermissions,
  onClose,
  onSaved,
}: {
  role: RoleRow;
  allPermissions: PermissionRow[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const codeToId = new Map(allPermissions.map((p) => [p.code, p.id]));
  const [selected, setSelected] = useState<Set<string>>(
    new Set(role.permission_codes.map((code) => codeToId.get(code)).filter((id): id is string => !!id)),
  );
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const byModule = new Map<string, PermissionRow[]>();
  for (const p of allPermissions) {
    if (!byModule.has(p.module)) byModule.set(p.module, []);
    byModule.get(p.module)!.push(p);
  }

  function toggle(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function handleSave() {
    setError(null);
    setIsSaving(true);
    try {
      await apiClient.put(`/roles/${role.id}/permissions`, { permission_ids: Array.from(selected) });
      onSaved();
      onClose();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to update permissions");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Permissions — {role.name}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3">
          {Array.from(byModule.entries()).map(([module, perms]) => (
            <div key={module}>
              <div className="mb-1 text-sm font-semibold capitalize">{module}</div>
              <div className="flex flex-col gap-1">
                {perms.map((p) => (
                  <label key={p.id} className="flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={selected.has(p.id)} onChange={() => toggle(p.id)} />
                    {p.action}
                  </label>
                ))}
              </div>
            </div>
          ))}
        </div>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <div className="flex gap-2">
          <Button type="button" onClick={handleSave} disabled={isSaving}>
            {isSaving ? "Saving..." : "Save Permissions"}
          </Button>
          <Button type="button" variant="outline" onClick={onClose}>
            Close
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function NewOrganizationForm({ onCreated }: { onCreated: () => void }) {
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [orgType, setOrgType] = useState("Plant");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await apiClient.post("/organizations", { name, code, org_type: orgType });
      setName("");
      setCode("");
      setOrgType("Plant");
      onCreated();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create organization");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3 border-b border-border pb-4">
      <div>
        <label className="mb-1 block text-sm font-medium" htmlFor="newOrgName">
          Name
        </label>
        <Input id="newOrgName" value={name} onChange={(e) => setName(e.target.value)} required />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium" htmlFor="newOrgCode">
          Code
        </label>
        <Input id="newOrgCode" value={code} onChange={(e) => setCode(e.target.value)} required />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium" htmlFor="newOrgType">
          Type
        </label>
        <Select id="newOrgType" value={orgType} onChange={(e) => setOrgType(e.target.value)}>
          <option value="Corporate">Corporate</option>
          <option value="BusinessUnit">BusinessUnit</option>
          <option value="Plant">Plant</option>
        </Select>
      </div>
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Creating..." : "Create Organization"}
      </Button>
      {error && <p className="w-full text-sm text-destructive">{error}</p>}
    </form>
  );
}

export default function AdminPage() {
  const { user: currentUser } = useAuth();
  const users = useApiQuery<UserRow[]>("/users", { page_size: 100 });
  const roles = useApiQuery<RoleRow[]>("/roles");
  const organizations = useApiQuery<OrganizationRow[]>("/organizations");
  const permissions = useApiQuery<PermissionRow[]>("/permissions");
  const [managingRoleId, setManagingRoleId] = useState<string | null>(null);
  const managingRole = (roles.data ?? []).find((r) => r.id === managingRoleId) ?? null;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold">Admin</h1>
        <p className="text-sm text-muted-foreground">Users, roles, and organizations (Identity & Access Management).</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Users</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <NewUserForm onCreated={users.refetch} />
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Username</TableHead>
                <TableHead>Full Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Roles</TableHead>
                <TableHead>Active</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(users.data ?? []).map((u) => (
                <TableRow key={u.id}>
                  <TableCell>{u.username}</TableCell>
                  <TableCell>{u.full_name}</TableCell>
                  <TableCell>{u.email}</TableCell>
                  <TableCell>{u.roles.join(", ") || "—"}</TableCell>
                  <TableCell>{u.is_active ? "Yes" : "No"}</TableCell>
                  <TableCell>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={u.id === currentUser?.id}
                      onClick={async () => {
                        try {
                          await apiClient.put(`/users/${u.id}`, { is_active: !u.is_active });
                          users.refetch();
                        } catch (err) {
                          alert(err instanceof ApiError ? err.message : "Failed to update user");
                        }
                      }}
                    >
                      {u.is_active ? "Deactivate" : "Activate"}
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Roles</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <NewRoleForm onCreated={roles.refetch} />
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Permissions</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(roles.data ?? []).map((r) => (
                  <TableRow key={r.id}>
                    <TableCell>{r.name}</TableCell>
                    <TableCell>{r.description ?? "—"}</TableCell>
                    <TableCell>{r.permission_codes.length}</TableCell>
                    <TableCell>
                      <Button size="sm" variant="outline" onClick={() => setManagingRoleId(r.id)}>
                        Manage
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Organizations</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <NewOrganizationForm onCreated={organizations.refetch} />
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Code</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(organizations.data ?? []).map((o) => (
                  <TableRow key={o.id}>
                    <TableCell>{o.code}</TableCell>
                    <TableCell>{o.name}</TableCell>
                    <TableCell>{o.org_type}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      {managingRole && (
        <RolePermissionsEditor
          role={managingRole}
          allPermissions={permissions.data ?? []}
          onClose={() => setManagingRoleId(null)}
          onSaved={roles.refetch}
        />
      )}
    </div>
  );
}
