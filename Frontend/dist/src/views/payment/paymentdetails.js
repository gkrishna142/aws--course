// paymentdetails.js
import React, { Fragment, useState, useEffect, forwardRef } from "react";
import { useDispatch, useSelector } from "react-redux";
import { fetchPayments } from "../../redux/paymentSlice";
import { fetchCourses } from "../../redux/courseSlice";
import ReactPaginate from "react-paginate";
import DataTable from "react-data-table-component";
import { ChevronDown } from "react-feather";
import '@styles/react/pages/student.scss';

import {
  Card,
  CardHeader,
  CardTitle,
  Input,
  Label,
  Row,
  Col,
  Button,
  Badge,
  Spinner
} from "reactstrap";

const formatDateTime = (value) => {
  if (!value) return "-";
  let normalized = value;
  if (normalized.includes(".")) {
    normalized = normalized.replace(/(\.\d{3})\d+/, "$1");
  }
  if (!normalized.endsWith("Z")) {
    normalized += "Z";
  }
  const date = new Date(normalized);
  if (isNaN(date)) return value;
  return date.toISOString().replace("T", ", ").split(".")[0];
};

const columns = [
  {
    name: 'Full Name',
    selector: row => row.name,
    sortable: true
  },
  {
    name: 'Email',
    selector: row => row.email,
    sortable: true
  },
  {
    name: 'Phone Number',
    selector: row => row.phone_number,
    sortable: true
  },
  {
    name: 'Enrolled Course(s) ',
    selector: (row) => {
      if (Array.isArray(row.course)) {
        return row.course.join(", ");
      }
      return row.course || "-";
    },
    sortable: true
  },
  {
    name: 'Batch (Weekdays/Weekend) ',
    selector: row =>
      Array.isArray(row.batch)
        ? row.batch.map(b => b.charAt(0).toUpperCase() + b.slice(1)).join(", ")
        : row.batch
          ? row.batch.charAt(0).toUpperCase() + row.batch.slice(1)
          : "",
    sortable: true
  },
  {
    name: 'Registration Date & Time',
    selector: row => formatDateTime(row.registration_dateTime),
    sortable: true
  },
  {
    name: "Status",
    cell: (row) => {
      const status = row.status?.toLowerCase(); // normalize
      let color = "light-secondary";
      if (row.status?.toLowerCase() === "pending") color = "light-warning";
      else if (row.status?.toLowerCase() === "failed") color = "light-danger";
      else if (row.status?.toLowerCase() === "completed") color = "light-success";
      else if (row.status?.toLowerCase() === "refunded") color = "light-primary";

      const label = status ? status.charAt(0).toUpperCase() + status.slice(1) : "-";

      return <Badge color={color}>{row.status || "-"}</Badge>;
    },
    sortable: true,
  },
  {
    name: 'Amount paid',
    selector: row => row.amount_paid,
    sortable: true
  },
  {
    name: 'Payment mode',
    selector: row => row.payment_method,
    sortable: true
  }
];

// Bootstrap Checkbox Component
const BootstrapCheckbox = forwardRef(({ onClick, ...rest }, ref) => (
  <div className="custom-control custom-checkbox">
    <input
      type="checkbox"
      className="custom-control-input"
      ref={ref}
      {...rest}
    />
    <label className="custom-control-label" onClick={onClick} />
  </div>
));

const PaymentDetails = () => {
  const dispatch = useDispatch();
  const { list: payments, loading, error } = useSelector(
    (state) => state.payments
  );
  const { list: courses, loading: courseLoading } = useSelector((state) => state.courses);

  // Local states
  const [currentPage, setCurrentPage] = useState(0);
  const [searchValue, setSearchValue] = useState("");
  const [selectedCourse, setSelectedCourse] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [filteredData, setFilteredData] = useState([]);
  const [showTable, setShowTable] = useState(false);
  const [tableData, setTableData] = useState([]);
  const [errors, setErrors] = useState({});

  // Fetch payments on mount
  useEffect(() => {
    dispatch(fetchPayments())
    dispatch(fetchCourses())
  }, [dispatch]);

  const validateForm = () => {
    let formErrors = {};

    if (!startDate) formErrors.startDate = "Start Date is required";
    if (!endDate) formErrors.endDate = "End Date is required";
    if (!selectedCourse) formErrors.selectedCourse = "Course is required";
    if (!selectedStatus) formErrors.selectedStatus = "Status is required";

    setErrors(formErrors);

    // return true if no errors
    return Object.keys(formErrors).length === 0;
  };

  const applyFilters = () => {
    let data = payments || [];

    // Map courseId -> courseName
    let selectedCourseName = null;
    if (selectedCourse) {
      const courseObj = courses.find(c => c.id === Number(selectedCourse));
      selectedCourseName = courseObj ? courseObj.name : null;
    }

    if (selectedCourseName) {
      data = data.filter(
        (item) => String(item.course).toLowerCase() === selectedCourseName.toLowerCase()
      );
    }

    // Status filter (respect dropdown input)
    if (selectedStatus) {
      data = data.filter(
        (item) => item.status?.toLowerCase() === selectedStatus.toLowerCase()
      );
    }

    // Date filters - always check registration_dateTime
    if (startDate) {
      data = data.filter((item) => {
        const itemDate = new Date(item.registration_dateTime);
        return itemDate >= new Date(startDate);
      });
    }

    if (endDate) {
      const end = new Date(endDate);
      end.setDate(end.getDate() + 1);
      data = data.filter((item) => {
        const itemDate = new Date(item.registration_dateTime);
        return itemDate < end;
      });
    }

    // Now apply the 3-day rule *per record*
    const today = new Date();
    data = data.filter((item) => {
      const regDate = new Date(item.registration_dateTime);
      const diffDays = Math.floor((today - regDate) / (1000 * 60 * 60 * 24));

      if (diffDays > 3) {
        // Older than 3 days → only completed allowed
        return item.status?.toLowerCase() === "completed";
      }
      return true; // within 3 days → allow whatever matches status filter
    });
    setFilteredData(data);
    setTableData(data);
  };

  const handleFilter = (e) => {
    const value = e.target.value.toLowerCase();
    setSearchValue(value);

    if (value.length) {
      const updatedData = payments.filter((item) =>
        Object.values(item).join(" ").toLowerCase().includes(value)
      );
      setFilteredData(updatedData);
      setTableData(updatedData);
    } else {
      applyFilters();
    }
  };

  // Pagination
  const handlePagination = (page) => setCurrentPage(page.selected);
  const CustomPagination = () => (
    <ReactPaginate
      previousLabel=""
      nextLabel=""
      forcePage={currentPage}
      onPageChange={handlePagination}
      pageCount={
        searchValue.length
          ? Math.ceil(filteredData.length / 7)
          : Math.ceil(payments.length / 7) || 1
      }
      breakLabel="..."
      pageRangeDisplayed={2}
      marginPagesDisplayed={2}
      activeClassName="active"
      pageClassName="page-item"
      breakClassName="page-item"
      breakLinkClassName="page-link"
      nextLinkClassName="page-link"
      nextClassName="page-item next"
      previousClassName="page-item prev"
      previousLinkClassName="page-link"
      pageLinkClassName="page-link"
      containerClassName="pagination react-paginate separated-pagination pagination-sm justify-content-end pr-1 mt-1"
    />
  );

  const convertArrayOfObjectsToCSV = (array) => {
    if (!array || !array.length) return null;

    const columnDelimiter = ",";
    const lineDelimiter = "\n";
    const keys = Object.keys(array[0]);
    let result = "";

    result += keys.join(columnDelimiter);
    result += lineDelimiter;

    array.forEach((item) => {
      let ctr = 0;
      keys.forEach((key) => {
        if (ctr > 0) result += columnDelimiter;

        //  Format only datetime fields
        if (
          ["registration_dateTime", "start_date_time", "end_date_time"].includes(key)
        ) {
          result += formatDateTime(item[key]);
        } else {
          result += item[key] ?? "-";
        }
        ctr++;
      });
      result += lineDelimiter;
    });

    return result;
  };

  const downloadCSV = (array) => {
    const link = document.createElement("a");
    let csv = convertArrayOfObjectsToCSV(array);
    if (!csv) return;

    const filename = "payments.csv";
    if (!csv.match(/^data:text\/csv/i)) {
      csv = `data:text/csv;charset=utf-8,${csv}`;
    }

    link.setAttribute("href", encodeURI(csv));
    link.setAttribute("download", filename);
    link.click();
  };

  return (
    <Fragment>
      <Card className="student-table-container">
        <CardHeader>
          <CardTitle tag="h4">Payment Details</CardTitle>
          <div className="d-flex mt-md-0 mt-1">
            <Button
              color="success"
              className=" payment-btn ml-1"
              onClick={() => {
                if (!filteredData || filteredData.length === 0) {
                  alert("No records to export");
                  return;
                }
                downloadCSV(filteredData)
              }}
            >
              Export CSV
            </Button>
          </div>
        </CardHeader>

        {/* Filter Form */}
        <Row className="px-4 pt-3 ps-2">
          <Col md="6" >
            <Label>Start Date</Label>
            <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} required />
            {errors.startDate && <small className="text-danger">{errors.startDate}</small>}
          </Col>
          <Col md="6">
            <Label>End Date</Label>
            <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} required />
            {errors.endDate && <small className="text-danger">{errors.endDate}</small>}
          </Col>
        </Row>

        <Row className="px-4 pt-3 ps-2">
          <Col md="6" >
            <Label>Course</Label>
            <Input type="select" value={selectedCourse} onChange={(e) => setSelectedCourse(e.target.value)} required>
              <option value="" disabled>Select course</option>
              {courseLoading ? (
                <option>Loading...</option>
              ) : (
                courses.map((course) => (
                  <option key={course.id} value={course.id}>
                    {course.name}
                  </option>
                ))
              )}
            </Input>
            {errors.selectedCourse && <small className="text-danger">{errors.selectedCourse}</small>}
          </Col>
          <Col md="6">
            <Label>Status</Label>
            <Input type="select" value={selectedStatus} onChange={(e) => setSelectedStatus(e.target.value)} required>
              <option value="" disabled>Select status</option>
              <option value="completed">Completed</option>
              <option value="pending">Pending</option>
              <option value="failed">Failed</option>
              <option value="refunded">Refunded</option>
            </Input>
            {errors.selectedStatus && <small className="text-danger">{errors.selectedStatus}</small>}
          </Col>
        </Row>

        <Row className="px-4 pt-3 mb-2">
          <Col className="d-flex align-items-end justify-content-end">
            <Button color="primary"
              onClick={() => {
                if (validateForm()) {
                  applyFilters();
                  setShowTable(true);
                } else {
                  setShowTable(false);
                }
              }}
            >Submit</Button>
          </Col>
        </Row>

        {showTable && (
          <>
            {loading ? (
              <div className="d-flex justify-content-center align-items-center" style={{ minHeight: "200px" }}>
                <Spinner color="primary" />
              </div>
            ) : error ? (
              <p className="p-2 text-danger">
                Error: {typeof error === "string" ? error : error.message || JSON.stringify(error)}
              </p>
            ) : tableData && tableData.length > 0 ? (
              <>
                <Row className="justify-content-end mx-0">
                  <Col md="3" sm="12" className="d-flex align-items-center justify-content-end mt-1">
                    <Input
                      id="search-input"
                      bsSize="sm"
                      type="text"
                      value={searchValue}
                      onChange={handleFilter}
                      placeholder="Search payments..."
                    />
                  </Col>
                </Row>

                <DataTable
                  noHeader
                  pagination
                  selectableRows
                  columns={columns}
                  data={tableData}
                  paginationPerPage={7}
                  className="react-dataTable"
                  sortIcon={<ChevronDown size={10} />}
                  paginationDefaultPage={currentPage + 1}
                  paginationComponent={CustomPagination}
                  selectableRowsComponent={BootstrapCheckbox}
                />
              </>
            ) : (
              <p className="text-center p-2 text-danger">No records found</p>
            )}
          </>
        )}
      </Card>
    </Fragment >
  );
};

export default PaymentDetails;