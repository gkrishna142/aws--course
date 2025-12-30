import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  setClassLevel,
  setOriginalPrice,
  setDiscount,
  reset,
  fetchCalculatePrice,
  fetchCourses,
} from "../../redux/priceSlice";

const PriceCalculator = () => {
  const dispatch = useDispatch();
  const {
    classLevel,
    originalPrice,
    discount,
    finalPrice,
    error,
    success,
    loading,
    courses,
  } = useSelector((state) => state.pricing);

  const [previewPrice, setPreviewPrice] = useState("");
  const [warning, setWarning] = useState("");

  // Fetch courses when component loads
  useEffect(() => {
    dispatch(fetchCourses());
  }, [dispatch]);

  // Calculate preview price
  useEffect(() => {
    const priceNum = parseFloat(originalPrice);
    const discountNum = parseFloat(discount);
    if (!isNaN(priceNum) && !isNaN(discountNum)) {
      const calcPrice =
        Math.round(
          (priceNum - priceNum * (discountNum / 100) + Number.EPSILON) * 100
        ) / 100;
      setPreviewPrice(calcPrice.toFixed(2));
    } else {
      setPreviewPrice("");
    }
  }, [originalPrice, discount]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!classLevel || !originalPrice || !discount) {
      setWarning("⚠ Please fill out all the fields.");
      return;
    }
    setWarning("");

    dispatch(
      fetchCalculatePrice({
        course: parseInt(classLevel, 10),
        original_price: parseFloat(originalPrice),
        discount_percent: parseFloat(discount),
        final_price: parseFloat(previewPrice),
      })
    );
  };

  useEffect(() => {
    if (success || error || warning) {
      const timer = setTimeout(() => {
        dispatch(reset());
        setWarning("");
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [success, error, warning, dispatch]);

  return (
    <div className="px-2 price-calculator">
      {(warning || success || error) && (
        <div
          className={`mx-auto mb-1 p-1 text-center fw-bold rounded ${
            warning
              ? "bg-light-warning text-dark"
              : success
              ? "bg-light-success text-white"
              : "bg-light-danger text-white"
          }`}
          style={{ maxWidth: "600px" }}
        >
          {warning ||
            (success ? "✅ Data submitted successfully!" : `❌ ${error}`)}
        </div>
      )}

      <h2
        className="mt-0 mb-2 text-center"
        style={{
          fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
          fontWeight: 700,
          fontSize: "2.6rem",
          letterSpacing: "0.5px",
        }}
      >
        Price Calculator
      </h2>
      <div style={{ width: "100%", display: "flex", flexDirection: "column", alignItems: "center" }}>
      <div className="mb-3 mt-1" style={{ maxWidth: "700px", width: "100%" }}>
        <label className="form-label fs-4 fw-bold ">Course</label>
        <select
          className="form-select price-calculator-field"
          value={classLevel || ""}
          onChange={(e) => dispatch(setClassLevel(e.target.value))}
        >
          <option value="">Select Course</option>
          {courses.length === 0 ? (
            <option disabled>Loading...</option>
          ) : (
            courses.map((course) => (
              <option key={course.id} value={course.id}>
                {course.name}
              </option>
            ))
          )}
        </select>
      </div>

      <div className="mb-3" style={{ maxWidth: "700px", width: "100%" }}>
        <label className="form-label fs-4 fw-bold">Original Price (₹)</label>
        <input
          type="text"
          className="form-control price-calculator-field"
          value={originalPrice}
          onChange={(e) => dispatch(setOriginalPrice(e.target.value))}
          placeholder="Enter original price"
        />
      </div>

      <div className="mb-3" style={{ maxWidth: "700px", width: "100%" }}>
        <label className="form-label fs-4 fw-bold">Discount (%)</label>
        <input
          type="text"
          className="form-control price-calculator-field"
          value={discount}
          onChange={(e) => dispatch(setDiscount(e.target.value))}
          placeholder="Enter discount percentage"
        />
      </div>

      <div className="mb-3" style={{ maxWidth: "700px", width: "100%" }}>
        <label className="form-label fs-4 fw-bold">Final Price (₹)</label>
        <input
          type="text"
          className="form-control price-calculator-field"
          value={previewPrice ? `₹${previewPrice}` : ""}
          readOnly
          placeholder="Final price will be shown"
          style={{ backgroundColor: "#f9f9f9" }}
        />
      </div>
      <button
        type="button"
        onClick={handleSubmit}
        className="btn btn-primary w-100 mb-0"
        disabled={loading}
        style={{ padding: "0.9rem", maxWidth: "300px", width: "100%" }}
      >
        {loading ? "Calculating..." : "Submit"}
      </button>
    </div>
    </div>
  );
};

export default PriceCalculator;