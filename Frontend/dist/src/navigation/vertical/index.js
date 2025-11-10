// ** Navigation imports
import dashboards from './dashboards'
import teachers from './teachers'
import students from './students'
import payments from './payments'
import calculator from './calculator'

// ** Merge & Export
export default [...dashboards, ...teachers, ...students, ...payments, ...calculator]
