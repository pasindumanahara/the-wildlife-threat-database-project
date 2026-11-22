const ALLOWED_EXTENSIONS = new Set(["pdf", "jpg", "jpeg", "png"]);

const ALLOWED_MIME_TYPES = new Set([
  "application/pdf",
  "image/jpeg",
  "image/png",
]);

const DANGEROUS_EXTENSIONS = new Set([
  "exe",
  "bat",
  "cmd",
  "sh",
  "msi",
  "dll",
  "scr",
  "pif",
  "com",
  "js",
  "mjs",
  "cjs",
  "jsx",
  "ts",
  "vbs",
  "ps1",
  "php",
  "phtml",
  "py",
  "rb",
  "pl",
  "jsp",
  "asp",
  "aspx",
  "html",
  "htm",
  "svg",
  "xml",
  "jar",
  "war",
  "hta",
  "zip",
  "rar",
  "7z",
  "tar",
  "gz",
]);

const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024;

// Checks the format and date code of a Sri Lankan NIC number.
export function validateNIC(nic) {
  if (typeof nic !== "string" || !nic.trim()) {
    return {isValid: false, error: "NIC number is required."};
  }

  const normalized = nic.trim().toUpperCase();
  const oldNicPattern = /^(\d{2})(\d{3})\d{4}[VX]$/;
  const newNicPattern = /^(\d{4})(\d{3})\d{5}$/;

  let dayOfYear = null;

  if (oldNicPattern.test(normalized)) {
    dayOfYear = parseInt(normalized.slice(2, 5), 10);
  } else if (newNicPattern.test(normalized)) {
    const birthYear = parseInt(normalized.slice(0, 4), 10);
    const currentYear = new Date().getFullYear();

    if (birthYear < 1900 || birthYear > currentYear) {
      return {isValid: false, error: "NIC contains an invalid birth year."};
    }

    dayOfYear = parseInt(normalized.slice(4, 7), 10);
  } else {
    return {
      isValid: false,
      error: "Enter a valid NIC (9 digits followed by V/X, or 12 digits).",
    };
  }

  const isValidMaleDay = dayOfYear >= 1 && dayOfYear <= 366;
  const isValidFemaleDay = dayOfYear >= 501 && dayOfYear <= 866;

  if (!isValidMaleDay && !isValidFemaleDay) {
    return {isValid: false, error: "NIC contains an invalid date code."};
  }

  return {isValid: true, error: null};
}

// Checks whether an office phone number uses a valid Sri Lankan format.
export function validateOfficePhone(phone) {
  if (typeof phone !== "string" || !phone.trim()) {
    return {isValid: false, error: "Office phone number is required."};
  }

  const cleaned = phone.trim().replace(/[\s\-()]/g, "");
  const slPhonePattern = /^(?:0|\+94|94)[1-9]\d{8}$/;

  if (!slPhonePattern.test(cleaned)) {
    return {
      isValid: false,
      error:
        "Enter a valid 10-digit Sri Lankan phone number (e.g., 0112345678 or +94112345678).",
    };
  }

  return {isValid: true, error: null};
}

// Checks the length and format of an email address.
export function validateEmail(email) {
  if (typeof email !== "string" || !email.trim()) {
    return {isValid: false, error: "Email address is required."};
  }

  const trimmed = email.trim();

  if (trimmed.length > 254) {
    return {isValid: false, error: "Email address is too long."};
  }

  const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

  if (!emailPattern.test(trimmed) || trimmed.includes("..")) {
    return {isValid: false, error: "Enter a valid email address."};
  }

  return {isValid: true, error: null};
}

// Checks password length, character requirements, and whitespace.
export function validatePassword(password) {
  if (typeof password !== "string" || !password) {
    return {isValid: false, error: "Password is required."};
  }

  if (password.length < 8) {
    return {
      isValid: false,
      error: "Password must be at least 8 characters long.",
    };
  }

  if (password.length > 128) {
    return {isValid: false, error: "Password cannot exceed 128 characters."};
  }

  if (/\s/.test(password)) {
    return {isValid: false, error: "Password cannot contain spaces."};
  }

  if (!/[A-Z]/.test(password)) {
    return {
      isValid: false,
      error: "Password must include at least one uppercase letter.",
    };
  }

  if (!/[a-z]/.test(password)) {
    return {
      isValid: false,
      error: "Password must include at least one lowercase letter.",
    };
  }

  if (!/\d/.test(password)) {
    return {
      isValid: false,
      error: "Password must include at least one number.",
    };
  }

  if (!/[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?~`]/.test(password)) {
    return {
      isValid: false,
      error: "Password must include at least one special character.",
    };
  }

  return {isValid: true, error: null};
}

// Identifies a PDF, JPEG, or PNG from its header bytes.
async function detectFileSignature(file) {
  const headerSlice = file.slice(0, 8);
  const buffer = await headerSlice.arrayBuffer();
  const bytes = new Uint8Array(buffer);

  if (
    bytes.length >= 5 &&
    bytes[0] === 0x25 &&
    bytes[1] === 0x50 &&
    bytes[2] === 0x44 &&
    bytes[3] === 0x46 &&
    bytes[4] === 0x2d
  ) {
    return "pdf";
  }

  if (
    bytes.length >= 3 &&
    bytes[0] === 0xff &&
    bytes[1] === 0xd8 &&
    bytes[2] === 0xff
  ) {
    return "jpeg";
  }

  if (
    bytes.length >= 8 &&
    bytes[0] === 0x89 &&
    bytes[1] === 0x50 &&
    bytes[2] === 0x4e &&
    bytes[3] === 0x47 &&
    bytes[4] === 0x0d &&
    bytes[5] === 0x0a &&
    bytes[6] === 0x1a &&
    bytes[7] === 0x0a
  ) {
    return "png";
  }

  return null;
}

// Checks a verification document’s name, size, file type, and signature.
export async function validateVerificationDocument(
  file,
  maxSizeBytes = MAX_FILE_SIZE_BYTES,
) {
  if (!file || !(file instanceof File)) {
    return {isValid: false, error: "Please upload a verification document."};
  }

  if (file.size === 0) {
    return {isValid: false, error: "The selected file is empty."};
  }

  if (file.size > maxSizeBytes) {
    const maxMB = (maxSizeBytes / (1024 * 1024)).toFixed(1);
    return {isValid: false, error: `File size must not exceed ${maxMB} MB.`};
  }

  const fileName = file.name;

  if (/[/\\]|\0|\.\./.test(fileName)) {
    return {isValid: false, error: "Invalid or suspicious file name detected."};
  }

  const parts = fileName.toLowerCase().split(".");
  if (parts.length < 2) {
    return {
      isValid: false,
      error: "File must have a valid extension (.pdf, .jpg, .jpeg, .png).",
    };
  }

  const extension = parts[parts.length - 1];

  const precedingSegments = parts.slice(1, -1);
  const hasDangerousSegment = precedingSegments.some((segment) =>
    DANGEROUS_EXTENSIONS.has(segment),
  );

  if (hasDangerousSegment) {
    return {isValid: false, error: "Suspicious file name rejected."};
  }

  if (!ALLOWED_EXTENSIONS.has(extension)) {
    return {
      isValid: false,
      error: "Only .pdf, .jpg, .jpeg, and .png files are allowed.",
    };
  }

  if (!ALLOWED_MIME_TYPES.has(file.type)) {
    return {
      isValid: false,
      error: "Unsupported or suspicious file type detected.",
    };
  }

  const detectedType = await detectFileSignature(file);
  const expectedType =
    extension === "jpg" || extension === "jpeg" ? "jpeg" : extension;

  if (!detectedType || detectedType !== expectedType) {
    return {
      isValid: false,
      error:
        "File content does not match its extension. Suspicious file declined.",
    };
  }

  return {isValid: true, error: null};
}

// Validates officer signup details and collects errors by field.
export async function validateOfficerForm(formData) {
  const errors = {};

  const nicResult = validateNIC(formData.nic);
  if (!nicResult.isValid) errors.nic = nicResult.error;

  const phoneResult = validateOfficePhone(formData.officePhone);
  if (!phoneResult.isValid) errors.officePhone = phoneResult.error;

  const emailResult = validateEmail(formData.email);
  if (!emailResult.isValid) errors.email = emailResult.error;

  const passwordResult = validatePassword(formData.password);
  if (!passwordResult.isValid) errors.password = passwordResult.error;

  const docResult = await validateVerificationDocument(
    formData.verificationDocument,
  );
  if (!docResult.isValid) errors.verificationDocument = docResult.error;

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  };
}

const ALLOWED_IMAGE_EXTENSIONS = new Set(["jpg", "jpeg", "png", "webp"]);

const ALLOWED_IMAGE_MIME_TYPES = new Set([
  "image/jpeg",
  "image/png",
  "image/webp",
]);

const DANGEROUS_IMAGE_EXTENSIONS = new Set([
  "exe",
  "bat",
  "cmd",
  "sh",
  "msi",
  "dll",
  "scr",
  "js",
  "mjs",
  "php",
  "phtml",
  "py",
  "rb",
  "jsp",
  "asp",
  "aspx",
  "html",
  "htm",
  "svg",
  "xml",
  "zip",
  "rar",
  "7z",
]);

const DEFAULT_OPTIONS = {
  required: false,
  maxSizeBytes: 2 * 1024 * 1024,
  minWidth: 100,
  minHeight: 100,
  maxWidth: 4096,
  maxHeight: 4096,
};

// Identifies a JPEG, PNG, or WebP image from its header bytes.
async function detectImageSignature(file) {
  const buffer = await file.slice(0, 12).arrayBuffer();
  const bytes = new Uint8Array(buffer);

  if (
    bytes.length >= 3 &&
    bytes[0] === 0xff &&
    bytes[1] === 0xd8 &&
    bytes[2] === 0xff
  ) {
    return "jpeg";
  }

  if (
    bytes.length >= 8 &&
    bytes[0] === 0x89 &&
    bytes[1] === 0x50 &&
    bytes[2] === 0x4e &&
    bytes[3] === 0x47 &&
    bytes[4] === 0x0d &&
    bytes[5] === 0x0a &&
    bytes[6] === 0x1a &&
    bytes[7] === 0x0a
  ) {
    return "png";
  }

  if (
    bytes.length >= 12 &&
    bytes[0] === 0x52 &&
    bytes[1] === 0x49 &&
    bytes[2] === 0x46 &&
    bytes[3] === 0x46 &&
    bytes[8] === 0x57 &&
    bytes[9] === 0x45 &&
    bytes[10] === 0x42 &&
    bytes[11] === 0x50
  ) {
    return "webp";
  }

  return null;
}

// Loads an image and returns its width and height.
function getImageDimensions(file) {
  return new Promise((resolve, reject) => {
    const objectUrl = URL.createObjectURL(file);
    const img = new Image();

    img.onload = () => {
      URL.revokeObjectURL(objectUrl);
      resolve({width: img.naturalWidth, height: img.naturalHeight});
    };

    img.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      reject(new Error("Image failed to decode."));
    };

    img.src = objectUrl;
  });
}

// Checks a profile photo’s name, size, type, content, and dimensions.
export async function validateProfilePhoto(file, customOptions = {}) {
  const options = {...DEFAULT_OPTIONS, ...customOptions};

  if (!file || !(file instanceof File)) {
    return options.required || file != null
      ? {isValid: false, error: "Please select a profile photo."}
      : {isValid: true, error: null};
  }

  if (file.size === 0) {
    return {isValid: false, error: "The selected image file is empty."};
  }

  if (file.size > options.maxSizeBytes) {
    const maxMB = (options.maxSizeBytes / (1024 * 1024)).toFixed(1);
    return {
      isValid: false,
      error: `Profile photo must be smaller than ${maxMB} MB.`,
    };
  }

  const fileName = file.name;

  if (/[/\\]|\0|\.\./.test(fileName)) {
    return {isValid: false, error: "Invalid or suspicious file name."};
  }

  const parts = fileName.toLowerCase().split(".");
  if (parts.length < 2) {
    return {
      isValid: false,
      error: "Image must have a valid extension (.jpg, .jpeg, .png, .webp).",
    };
  }

  const extension = parts[parts.length - 1];
  const precedingSegments = parts.slice(1, -1);

  if (
    precedingSegments.some((segment) => DANGEROUS_IMAGE_EXTENSIONS.has(segment))
  ) {
    return {isValid: false, error: "Suspicious file name rejected."};
  }

  if (!ALLOWED_IMAGE_EXTENSIONS.has(extension)) {
    return {
      isValid: false,
      error: "Only .jpg, .jpeg, .png, and .webp images are allowed.",
    };
  }

  if (!ALLOWED_IMAGE_MIME_TYPES.has(file.type)) {
    return {isValid: false, error: "Unsupported or suspicious image type."};
  }

  const detectedType = await detectImageSignature(file);
  const expectedType =
    extension === "jpg" || extension === "jpeg" ? "jpeg" : extension;

  if (!detectedType || detectedType !== expectedType) {
    return {
      isValid: false,
      error:
        "File content does not match its extension. Suspicious file declined.",
    };
  }

  try {
    const {width, height} = await getImageDimensions(file);

    if (width < options.minWidth || height < options.minHeight) {
      return {
        isValid: false,
        error: `Image must be at least ${options.minWidth}x${options.minHeight} pixels.`,
      };
    }

    if (width > options.maxWidth || height > options.maxHeight) {
      return {
        isValid: false,
        error: `Image dimensions must not exceed ${options.maxWidth}x${options.maxHeight} pixels.`,
      };
    }
  } catch {
    return {
      isValid: false,
      error: "The selected file is not a valid or readable image.",
    };
  }

  return {isValid: true, error: null};
}
