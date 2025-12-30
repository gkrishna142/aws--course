
import { Container, Row, Col } from "reactstrap"
import ApexBarChart from "./BarChart/"
import Transactions from "./Transactions"
import UsersStatusPieChart from "./PieChart"
import UnenrolledStudentsTable from "./StudentsTable"

const Dashboard = () => {
  return (
    <Container>
      <Row className="mb-3">
        <Col>
          <h4>Dashboard</h4>
        </Col>
      </Row>
      <Row>
         <Col md="6">
          <ApexBarChart />
        </Col> 
        <Col md="6">
          < UsersStatusPieChart/>  
        </Col> 
        
      </Row>
      <Row>
      <Col md="6" lg="6">
          <Transactions />  
        </Col>
        <Col md="6" lg="6">
          <UnenrolledStudentsTable />  
        </Col>
      </Row>
    </Container>
  )
}

export default Dashboard
