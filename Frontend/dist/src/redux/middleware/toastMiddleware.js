// src/redux/middleware/toastMiddleware.js
import toast from "react-hot-toast";

const toastMiddleware = () => (next) => (action) => {
  // Show success messages when thunk resolves
  if (action.type.endsWith("/fulfilled")) {
    const message = action.payload?.message;
    const type = action.payload?.message_type || "success";

    if (message) {
      if (type === "success") toast.success(message);
      else if (type === "info") toast(message, { icon: "ℹ️" });
      else if (type === "warning") toast(message, { icon: "⚠️" });
      else toast.success(message);
    }
  }

  // Show error messages when thunk fails
  if (action.type.endsWith("/rejected")) {
    let message =
      action.payload?.message ||
      action.error?.message ||
      null;
    if (message && typeof message === "object") {
      try {
        message = Object.values(message).flat(Infinity).join("\n");
      } catch {
        message = JSON.stringify(message);
      }
    }
    if (message) {
      toast.error(message);
    }
  }

  return next(action);
};

export default toastMiddleware;
