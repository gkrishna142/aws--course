import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import Chart from "react-apexcharts";
import { Card, CardHeader, CardTitle, CardBody, CardSubtitle, Spinner } from "reactstrap";
import { fetchUsersByCourse } from "../../../redux/analyticsSlice";



const ApexBarChart = () => {
  const dispatch = useDispatch();
  const { studentEnrollList = [], loading, errorUsers } = useSelector((state) => state.dashboard || {});

  useEffect(() => {
    dispatch(fetchUsersByCourse());
  }, [dispatch]);

  // console.log("studentEnrollList", studentEnrollList);

  // Use correct keys from your API
   const categories = studentEnrollList.map((item) => item.name);
   const values = studentEnrollList.map((item) => item.student_count);
  // const categories = studentEnrollList?.map((item) => item.name) || [];
  // const values = studentEnrollList?.map((item) => item.student_count) || [];
  
  const options = {
    chart: { type: "bar", toolbar: { show: false } },
    plotOptions: { bar: { horizontal: false, columnWidth: "40%", borderRadius: 6, distributed: true } },
    colors: ["#7367F0", "#28C76F", "#FF9F43", "#EA5455", "#00CFE8"],
    dataLabels: { enabled: false },
    grid: { borderColor: "#f1f1f1" },
    xaxis: { categories, labels: { style: { fontSize: "13px", fontWeight: 500 } } },
    yaxis: { labels: { style: { fontSize: "13px" } } },
    tooltip: { theme: "dark" },
  };

  const series = [{ name: "Users", data: values }];

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle className="fw-bolder" tag="h4">Users by Course</CardTitle>
        </div>
      </CardHeader>
      <CardBody className="d-flex justify-content-center align-items-center" style={{ minHeight: "440px" }}>
        {loading ? (
          <Spinner color="primary" />
        ) : errorUsers ? (
          <p className="text-danger text-center ">{errorUsers}</p>
        ) : (
          <Chart options={options} series={series} type="bar" height={400} />
        )}
      </CardBody>
    </Card>
  );
};

export default ApexBarChart;