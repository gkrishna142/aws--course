// ** React Imports
import { Fragment, useState, forwardRef, useEffect } from 'react'
import { Badge } from 'reactstrap'
import '@styles/react/pages/teacher.scss';


// ** Add New Modal Component
import AddNewModal from './addteacherdetails'

// ** Redux Imports
import { useDispatch, useSelector } from 'react-redux'
import { fetchTeachers } from '../../redux/teacherSlice'

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


// ** Table Columns
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
    name: 'Phone',
    selector: row => row.phone,
    sortable: true
  },
  {
    name: 'Courses',
    selector: row => (row.course_assigned ? row.course_assigned.join(", ") : ""),
    sortable: true
  },
  {
    name: 'Batch (Weekdays/Weekend)',
    // selector: row => row.batches.join(", "),
    selector: row => {
      if (!row.batches) return "";
      return row.batches
        .map(batch => {
          if (typeof batch === "string") return batch;
          // batch is an object, format it nicely
          if (batch.type === "weekdays") {
            return `Weekdays: ${batch.weekdays_start} - ${batch.weekdays_end}`;
          } else if (batch.type === "weekends") {
            return `Weekend: ${batch.saturday_start || ""}-${batch.saturday_end || ""}, ${batch.sunday_start || ""}-${batch.sunday_end || ""}`;
          } else {
            return JSON.stringify(batch);
          }
        })
        .join(", ");
    },
    sortable: true
  },

  {
    name: 'Status',
    selector: row => row.status,
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

const TeacherDetails = () => {
  const dispatch = useDispatch();
  const { list, loading, error } = useSelector((state) => state.teachers);

  // ** States
  const [modal, setModal] = useState(false)
  const [currentPage, setCurrentPage] = useState(0)
  const [searchValue, setSearchValue] = useState('')
  const [filteredData, setFilteredData] = useState([])

  const API_URL = import.meta.env.VITE_API_BASE_URL
  const token = localStorage.getItem('token')

  // ** Fetch teachers on load
  useEffect(() => {
    dispatch(fetchTeachers())
  }, [dispatch])

  // ** Modal toggle
  const handleModal = () => setModal(!modal)

  // ** Filter
  const handleFilter = e => {
    const value = e.target.value
    setSearchValue(value)
    if (value.length) {
      const updatedData = list.filter(item =>
        (item.name && item.name.toLowerCase().includes(value.toLowerCase())) ||
        (item.email && item.email.toLowerCase().includes(value.toLowerCase())) ||
        (item.subject && item.subject.toLowerCase().includes(value.toLowerCase()))
      )
      setFilteredData(updatedData)
    } else {
      setFilteredData([])
    }
  }

  // ** Pagination
  const handlePagination = page => {
    setCurrentPage(page.selected)
  }

  // ** Custom Pagination
  const CustomPagination = () => (
    <ReactPaginate
      previousLabel=''
      nextLabel=''
      forcePage={currentPage}
      onPageChange={handlePagination}
      pageCount={searchValue.length ? Math.ceil(filteredData.length / 7) : Math.ceil(list.length / 7) || 1}
      breakLabel='...'
      pageRangeDisplayed={2}
      marginPagesDisplayed={2}
      activeClassName='active'
      pageClassName='page-item'
      breakClassName='page-item'
      breakLinkClassName='page-link'
      nextLinkClassName='page-link'
      nextClassName='page-item next'
      previousClassName='page-item prev'
      previousLinkClassName='page-link'
      pageLinkClassName='page-link'
      containerClassName='pagination react-paginate separated-pagination pagination-sm justify-content-end pr-1 mt-1'
    />
  )

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
    const filename = 'teachers.csv'
    if (!csv.match(/^data:text\/csv/i)) {
      csv = `data:text/csv;charset=utf-8,${csv}`
    }
    link.setAttribute('href', encodeURI(csv))
    link.setAttribute('download', filename)
    link.click()
  }

  return (
    <Fragment>
      <Card className="teacher-table-container">
        <CardHeader className='flex-md-row flex-column align-md-items-center align-items-start border-bottom'>
          <CardTitle tag='h4'>Teacher Details</CardTitle>
          <div className='d-flex mt-md-0 mt-1'>
            <Button color='primary' onClick={handleModal}>
              <span className='teacher-btn align-middle ml-50'>Add Instructor</span>
            </Button >
            <Button color='success' className='teacher-btn ms-1' onClick={() => downloadCSV(searchValue.length ? filteredData : list)}>
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
          <p className='p-2 text-danger text-center'>Error: {error}</p>
        ) : (

          <DataTable
            noHeader
            pagination
            selectableRows
            columns={columns}
            paginationPerPage={7}
            className='react-dataTable'
            sortIcon={<ChevronDown size={10} />}
            paginationDefaultPage={currentPage + 1}
            paginationComponent={CustomPagination}
            data={searchValue.length ? filteredData : (list || [])}
            selectableRowsComponent={BootstrapCheckbox}
            responsive={true}
          />
        )}
      </Card>

      <AddNewModal open={modal} handleModal={handleModal} />
    </Fragment>
  )
}

export default TeacherDetails



