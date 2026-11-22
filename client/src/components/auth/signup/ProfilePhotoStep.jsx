import {useEffect, useRef} from "react";
import {FileUpload} from "../../common/FileUpload";
import profilePlaceholder from "../../../assets/images/profile-placeholder.jpg";

export function ProfilePhotoStep({photo, onPhoto, fullName, email, accountType}) {
  const preview = useRef(null);
  useEffect(function loadPreview() {
    if (!photo) return;
    const url = URL.createObjectURL(photo);
    preview.current.src = url;
    return function releasePreview() { URL.revokeObjectURL(url); };
  }, [photo]);
  return (
    <div className="grid min-w-0 items-stretch gap-6 @lg:grid-cols-2">
      <div className="flex min-h-full min-w-0 items-center gap-4 rounded-xl border border-zinc-200 p-4 sm:p-5">
        <div className="size-20 shrink-0 overflow-hidden rounded-full border border-zinc-300 bg-zinc-100 sm:size-24">
          <img ref={preview} src={profilePlaceholder} alt={photo ? "Selected profile photo" : "Profile placeholder"} className="size-full object-cover" />
        </div>
        <div className="min-w-0 space-y-1">
          <p className="truncate font-semibold text-zinc-950">{fullName.trim().split(/\s+/).slice(0, 2).join(" ") || "Your name"}</p>
          <p className="break-all text-sm text-zinc-600">{email || "Your email address"}</p>
          <p className="text-sm text-zinc-600">{accountType === "officer" ? "Government officer" : "Regular user"}</p>
        </div>
      </div>
      <FileUpload type="photo" label="Choose a profile photo (optional)" description="You can add a profile photo later." accept="image/*" file={photo} onSelect={onPhoto} className="h-full" />
    </div>
  );
}
