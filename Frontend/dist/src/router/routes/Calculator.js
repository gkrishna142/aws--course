import { lazy } from "react";

const Calculator = lazy(() => import("../../views/Calculator"));

const CalculatorRoutes = [
  {
    path: "/pricecalculator",
    element: <Calculator />
  }
];

export default CalculatorRoutes;
