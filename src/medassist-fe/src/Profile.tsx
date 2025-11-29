import React from "react";

export function UserProfile({ profile, setProfile }: any) {
  const [editing, setEditing] = React.useState(false);

  // Load from localStorage on mount
  React.useEffect(() => {
    const saved = localStorage.getItem("userProfile");
    if (saved) setProfile(JSON.parse(saved));
  }, []);

  // Save to localStorage on change
  const saveProfile = () => {
    localStorage.setItem("userProfile", JSON.stringify(profile));
    setEditing(false);
  };

  const resetProfile = () => {
    setProfile({});
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>): void => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      saveProfile();
    }
  };

  return (
    <div
      style={{
        padding: "12px",
        paddingLeft: 0,
        // border: "1px solid #ddd",
        borderRadius: "8px",
        marginBottom: "12px",
        background: "transparent",
      }}
    >
      {editing ? (
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <input
            type="text"
            placeholder="Jméno a příjmení"
            value={profile.fullName}
            onChange={(e) =>
              setProfile({ ...profile, fullName: e.target.value })
            }
            onKeyDown={handleKeyDown}
          />

          <input
            type="text"
            placeholder="Osobní číslo"
            value={profile.personalNumber}
            onChange={(e) =>
              setProfile({ ...profile, personalNumber: e.target.value })
            }
            onKeyDown={handleKeyDown}
          />

          <input
            type="text"
            placeholder="Osobní číslo"
            value={profile.department}
            onChange={(e) =>
              setProfile({ ...profile, department: e.target.value })
            }
            onKeyDown={handleKeyDown}
          />

          <input
            type="text"
            placeholder="Telefon / e-mail"
            value={profile.contact}
            onChange={(e) =>
              setProfile({ ...profile, contact: e.target.value })
            }
            onKeyDown={handleKeyDown}
          />

          <button onClick={saveProfile}>Uložit</button>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          <div>
            <strong>Jméno:</strong> {profile.fullName || "—"}
          </div>
          <div>
            <strong>Osobní číslo:</strong> {profile.personalNumber || "—"}
          </div>
          <div>
            <strong>Útvar:</strong> {profile.department || "—"}
          </div>
          <div>
            <strong>Kontakt:</strong> {profile.contact || "—"}
          </div>

          <button style={{ marginTop: "8px" }} onClick={() => setEditing(true)}>
            Upravit profil
          </button>
          <button style={{ marginTop: "8px" }} onClick={() => resetProfile()}>
            Smazat
          </button>
        </div>
      )}
    </div>
  );
}
