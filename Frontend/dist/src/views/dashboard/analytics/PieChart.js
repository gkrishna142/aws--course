// src/views/dashboard/analytics/PieChart.js
import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import Chart from "react-apexcharts";
import { Card, CardHeader, CardTitle, CardBody, CardSubtitle, Spinner } from "reactstrap";
import { fetchUsersByStatus } from "../../../redux/analyticsSlice";

const UsersStatusPieChart = () => {
  const dispatch = useDispatch();
  const { usersByStatus = {}, loadingUsersByStatus, errorUsersByStatus } = useSelector(
    (state) => state.dashboard || {}
  );

  useEffect(() => {
    dispatch(fetchUsersByStatus());
  }, [dispatch]);
  // console.log("usersByStatus", usersByStatus);

  // Transform API object into array
  const transformedData = Array.isArray(usersByStatus)
    ? usersByStatus
    : [
        { status: "Active Users", count: usersByStatus.active_users || 0 },
        { status: "Registered Users", count: usersByStatus.registered_users || 0 },
        { status: "Deactivated Users", count: usersByStatus.deactivated_users || 0 },
      ];

  const labels = transformedData.map((item) => item.status);
  const series = transformedData.map((item) => item.count);

  const options = {
    chart: { type: "pie", toolbar: { show: false } },
    labels,
    colors: ["#28C76F", "#7367F0", "#EA5455"],
    dataLabels: { enabled: true },
    legend: { position: "bottom" },
    tooltip: { theme: "dark" },
  };

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle className="fw-bolder" tag="h4">Users by Status</CardTitle>
        </div>
      </CardHeader>
      <CardBody className="d-flex justify-content-center align-items-center" style={{ minHeight: "440px" }}>
        {loadingUsersByStatus ? (
          <Spinner color="primary" />
        ) : errorUsersByStatus ? (
          <p className="text-danger text-center fw-bold">{errorUsersByStatus}</p>
        ) : series.length === 0 ? (
          <p className="text-danger text-center fw-bold">No data available.</p>
        ) : (
          <Chart options={options} series={series} type="pie" height={450} />
        )}
      </CardBody>
    </Card>
  );
};


export default UsersStatusPieChart;
