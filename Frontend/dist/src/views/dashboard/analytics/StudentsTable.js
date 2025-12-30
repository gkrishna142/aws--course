import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  Card,
  CardHeader,
  CardTitle,
  CardSubtitle,
  CardBody,
  Table,
  Spinner,
} from "reactstrap";
import { fetchUnenrolledStudents } from "../../../redux/analyticsSlice";

const UnenrolledStudentsTable = () => {
  const dispatch = useDispatch();

  const {
    unenrolledStudents,
    loadingUnenrolled,
    errorUnenrolled,
  } = useSelector((state) => state.dashboard || {});

  useEffect(() => {
    dispatch(fetchUnenrolledStudents());
  }, [dispatch]);

  // Debug: Check what the data looks like
  // console.log("unenrolledStudents:", unenrolledStudents);

  const studentsArray = Array.isArray(unenrolledStudents)
    ? unenrolledStudents
    : [];

  return (
    <Card>
      <CardHeader>
        <CardTitle tag="h4">
          Students Registered but Not Enrolled
        </CardTitle>
      </CardHeader>
      <CardBody style={{ height: "290px", overflowY: "auto" }}>
        {loadingUnenrolled ? (
          <div className="d-flex justify-content-center align-items-center"
      style={{ height: "100%", width: "100%" }}>
            <Spinner color="primary" />
          </div>
        ) : errorUnenrolled ? (
          <p className="text-danger text-center fw-bold">{errorUnenrolled}</p>
        ) : studentsArray.length === 0 ? (
          <p className="text-danger text-center fw-bold">No unenrolled students found.</p>
        ) : (
          <Table responsive hover>
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Phone Number</th>
                <th>Registration Date</th>
                <th>Remaining Days</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {studentsArray.map((student, idx) => (
                <tr key={idx}>
                  <td>{student.name}</td>
                  <td>{student.email}</td>
                  <td>{student.phone_number}</td>
                  <td>
                    {new Date(student.registration_dateTime).toLocaleDateString()}
                  </td>
                  <td>{student.remaining_days ?? "N/A"}</td>
                  <td>{student.status}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </CardBody>
    </Card>
  );
};

export default UnenrolledStudentsTable;
