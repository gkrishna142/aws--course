// ** React Imports
import React, { Fragment, useState, useEffect, forwardRef } from "react";
import { useDispatch, useSelector } from "react-redux";
import { fetchStudents } from "../../redux/studentSlice";
import { Badge } from 'reactstrap'
import '@styles/react/pages/student.scss';

// ** Third Party Components
import ReactPaginate from 'react-paginate'
import DataTable from 'react-data-table-component'
import { ChevronDown } from 'react-feather'
import {
  Card,
  CardHeader,
  CardTitle,
  Button,
  Input,
  Label,
  Row,
  Col,
  Spinner
} from 'reactstrap'

// ** Sample Table Columns
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
    selector: row => row.phone,
    sortable: true
  },
  {
    name: 'Enrolled Course(s) ',
    selector: row =>
      row.enrolled_courses.join(", "),
    sortable: true
  },
  {
    name: 'Batch (Weekdays/Weekend) ',
    selector: row =>
      Array.isArray(row.batches)
        ? row.batches.map(b => b.charAt(0).toUpperCase() + b.slice(1)).join(", ")
        : row.batches
          ? row.batches.charAt(0).toUpperCase() + row.batches.slice(1)
          : "",
    sortable: true
  },
  {
    name: 'Registration Date & ',
    selector: row => row.registration_date,
    sortable: true
  },
  {
    name: 'Status',
    cell: row => (
      <Badge color={row.status ? 'light-success' : 'light-danger'}>
        {row.status ? 'Active' : 'Inactive'}
      </Badge>
    ),
    sortable: true
  }
]

// ** Bootstrap Checkbox Component
const BootstrapCheckbox = forwardRef(({ onClick, ...rest }, ref) => (
  <div className='custom-control custom-checkbox'>
    <input type='checkbox' className='custom-control-input' ref={ref} {...rest} />
    <label className='custom-control-label' onClick={onClick} />
  </div>
))
const DataTableWithButtons = () => {
  const dispatch = useDispatch();
  const { list: data, loading, error } = useSelector((state) => state.students);

  const [currentPage, setCurrentPage] = useState(0);
  const [searchValue, setSearchValue] = useState("");
  const [filteredData, setFilteredData] = useState([]);

  // Fetch students on component load
  useEffect(() => {
    dispatch(fetchStudents()).then((res) => {
      ;
      // console.log("Fetched students:", res.payload);
    });
  }, [dispatch]);

  // Filtering logic
  const handleFilter = (e) => {
    const value = e.target.value;
    setSearchValue(value);
    if (value.length) {
      const updatedData = data.filter((item) =>
        Object.values(item)
          .join(" ")
          .toLowerCase()
          .includes(value.toLowerCase())
      );
      setFilteredData(updatedData);
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
      pageCount={searchValue.length ? Math.ceil(filteredData.length / 7) : Math.ceil(data.length / 7) || 1}
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

  // ** CSV Export functions
  const convertArrayOfObjectsToCSV = array => {
    if (!array || !array.length) return null
    const columnDelimiter = ','
    const lineDelimiter = '\n'
    const keys = Object.keys(array[0])
    let result = ''
    result += keys.join(columnDelimiter)
    result += lineDelimiter
    array.forEach(item => {
      let ctr = 0
      keys.forEach(key => {
        if (ctr > 0) result += columnDelimiter
        result += item[key]
        ctr++
      })
      result += lineDelimiter
    })
    return result
  }

  const downloadCSV = array => {
    const link = document.createElement('a')
    let csv = convertArrayOfObjectsToCSV(array)
    if (!csv) return
    const filename = 'students.csv'
    if (!csv.match(/^data:text\/csv/i)) {
      csv = `data:text/csv;charset=utf-8,${csv}`
    }
    link.setAttribute('href', encodeURI(csv))
    link.setAttribute('download', filename)
    link.click()
  }

  return (
    <Fragment>
      <Card className="student-table-container">
        <CardHeader>
          <CardTitle tag="h4">Student Details</CardTitle>
          <div className='d-flex mt-md-0 mt-1'>
            <Button
              color="success" className="student-btn ml-1" onClick={() => downloadCSV(searchValue.length ? filteredData : data)}>
              Export CSV
            </Button>
          </div>
        </CardHeader>
        <Row className='justify-content-end mx-0'>
          <Col md='3' sm='12' className='d-flex align-items-center justify-content-end mt-1'>
            <Label for='search-input' className='mr-1'></Label>
            <Input
              id='search-input'
              bsSize='sm'
              type='text'
              className='dataTable-filter mb-50'
              value={searchValue}
              onChange={handleFilter}
              placeholder="Search teacher..."
            />
          </Col>
        </Row>

        {loading ? (
          <div className="d-flex justify-content-center align-items-center" style={{ minHeight: "200px" }}>
            <Spinner color="primary" />
          </div>
        ) : error ? (
          <p className="text-danger text-center">
            {typeof error === "string"
              ? error
              : typeof error === "object" && error.message
                ? error.message
                : JSON.stringify(error)}
          </p>
        ) : data && data.length > 0 ? (
          <DataTable
            noHeader
            pagination
            selectableRows
            columns={columns}
            paginationPerPage={7}
            className="react-dataTable"
            sortIcon={<ChevronDown size={10} />}
            paginationDefaultPage={currentPage + 1}
            paginationComponent={CustomPagination}
            data={searchValue.length ? filteredData : data || []}
            selectableRowsComponent={BootstrapCheckbox}

          />
        ) : (
          <p className="text-center p-2 text-danger"> {data?.message || "No records found"}</p>
        )}
      </Card>
    </Fragment>
  );
};

export default DataTableWithButtons;