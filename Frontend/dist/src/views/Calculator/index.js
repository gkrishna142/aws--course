import React from "react";
import PriceCalculator from "./PriceCalculator";

function CalculatorApp() {
  return (
    <div className="px-3 py-2 d-flex justify-content-center align-items-center" style={{backgroundcolor:'#2b3248'}}>
      <div className="col-12">
        <div
          className="card shadow-lg border-0 rounded-4 p-3 price-calculator-card"
          style={{
            minHeight: "800px",
            width: "100%", 
            margin: "0 auto",
            padding: "2.5rem 3rem",
          }}
        >
          <PriceCalculator />
        </div>
      </div>
    </div>
  );
}

export default CalculatorApp;