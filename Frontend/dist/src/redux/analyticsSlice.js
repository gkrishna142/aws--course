import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import axios from "axios";
import apiList from "../../api.json";
import api from "../utility/api"

const API_URL = import.meta.env.VITE_API_BASE_URL;

// --------------------- Thunks ---------------------

// Fetch student count by course (BarChart)
export const fetchUsersByCourse = createAsyncThunk(
  "dashboard/fetchUsersByCourse",
  async (_, { getState, rejectWithValue }) => {
    try {
      const token = getState().auth?.token || localStorage.getItem("access");
      if (!token) return rejectWithValue("No auth token found");

      const response = await api.get(`${API_URL}${apiList.barchart.studentCount}`, {
        headers: { Authorization: `Bearer ${token}` },
      });


      return response.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.message || err.response?.data?.detail || err.message);
    }
  }
);

// Fetch last 5 transactions
export const fetchTransactionsReport = createAsyncThunk(
  "dashboard/fetchTransactionsReport",
  async (_, { getState, rejectWithValue }) => {
    try {
      const token = getState().auth?.token || localStorage.getItem("access");
      if (!token) return rejectWithValue("No auth token found");

      const response = await api.get(`${API_URL}${apiList.payments.transactionsReport}`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { limit: 5 },
      });

      return response.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.message || err.response?.data?.detail || err.message);
    }
  }
);

// Fetch users by status for Pie Chart
export const fetchUsersByStatus = createAsyncThunk(
  "dashboard/fetchUsersByStatus",
  async (_, { getState, rejectWithValue }) => {
    try {
      const token = getState().auth?.token || localStorage.getItem("access");
      if (!token) return rejectWithValue("No auth token found");

      const response = await api.get(`${API_URL}${apiList.users.statusCount}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      return response.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.message || err.response?.data?.detail || err.message);
    }
  }
);
// Fetch unenrolled students
export const fetchUnenrolledStudents = createAsyncThunk(
  "dashboard/fetchUnenrolledStudents",
  async (_, { getState, rejectWithValue }) => {
    try {
      const token = getState().auth?.token || localStorage.getItem("access");
      if (!token) return rejectWithValue("No auth token found");

      const url = `${API_URL}${apiList.students.unenrolled}`;
      // console.log("[DEBUG] Fetching unenrolled students from:", url);
    

      const response = await api.get(url, {
        headers: { Authorization: `Bearer ${token}` },
      });

      return response.data;
    } catch (err) {
      // console.error("[ERROR] fetchUnenrolledStudents:", err);
      return rejectWithValue(err.response?.data?.message || err.response?.data?.detail || err.message);
    }
  }
);

// --------------------- Slice ---------------------

const initialState = {
  studentEnrollList: [],
  loading: false,
  errorUsers: null,

  transactions: [],
  loadingTransactions: false,
  errorTransactions: null,

  usersByStatus: [],
  loadingUsersByStatus: false,
  errorUsersByStatus: null,

  unenrolledStudents: [],
  loadingUnenrolled: false,
  errorUnenrolled: null,
};

const analyticsSlice = createSlice({
  name: "dashboard",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    // Users by Course
    builder
      .addCase(fetchUsersByCourse.pending, (state) => {
        state.loading = true;
        state.errorUsers = null;
      })
      .addCase(fetchUsersByCourse.fulfilled, (state, action) => {
        state.loading = false;
        // Normalization: pick correct array from payload
        if (Array.isArray(action.payload)) {
          state.studentEnrollList = action.payload;
        } else if (Array.isArray(action.payload?.data)) {
          state.studentEnrollList = action.payload.data;
        } else {
          state.studentEnrollList = [];
        }

      })
      .addCase(fetchUsersByCourse.rejected, (state, action) => {
        state.loading = false;
        state.errorUsers = action.payload || action.error.message;
      });

    // Transactions Report
    builder
      .addCase(fetchTransactionsReport.pending, (state) => {
        state.loadingTransactions = true;
        state.errorTransactions = null;
      })
      .addCase(fetchTransactionsReport.fulfilled, (state, action) => {
        state.loadingTransactions = false;
        if (Array.isArray(action.payload)) {
          state.transactions = action.payload;
        } else if (Array.isArray(action.payload?.data)) {
          state.transactions = action.payload.data;
        } else if (Array.isArray(action.payload?.results)) {
          state.transactions = action.payload.results;
        } else {
          state.transactions = [];
        }
      })
      .addCase(fetchTransactionsReport.rejected, (state, action) => {
        state.loadingTransactions = false;
        state.errorTransactions = action.payload || action.error.message;
      });

    // Users by Status (Pie Chart)
    builder
      .addCase(fetchUsersByStatus.pending, (state) => {
        state.loadingUsersByStatus = true;
        state.errorUsersByStatus = null;
      })
      .addCase(fetchUsersByStatus.fulfilled, (state, action) => {
        state.loadingUsersByStatus = false;
        if (Array.isArray(action.payload)) {
          state.usersByStatus = action.payload;
        } else if (Array.isArray(action.payload?.data)) {
          state.usersByStatus = action.payload.data;
        } else if (action.payload?.data && typeof action.payload.data === "object") {
          state.usersByStatus = action.payload.data; // keep object for charts
        } else if (action.payload && typeof action.payload === "object") {
          state.usersByStatus = action.payload;
        } else {
          state.usersByStatus = [];
        }
      })
      .addCase(fetchUsersByStatus.rejected, (state, action) => {
        state.loadingUsersByStatus = false;
        state.errorUsersByStatus = action.payload || action.error.message;
      });

    // Unenrolled Students
    builder
      .addCase(fetchUnenrolledStudents.pending, (state) => {
        state.loadingUnenrolled = true;
        state.errorUnenrolled = null;
      })
      .addCase(fetchUnenrolledStudents.fulfilled, (state, action) => {
        state.loadingUnenrolled = false;
        if (Array.isArray(action.payload)) {
          state.unenrolledStudents = action.payload;
        } else if (Array.isArray(action.payload?.data)) {
          state.unenrolledStudents = action.payload.data;
        } else {
          state.unenrolledStudents = [];
        }
      })
      .addCase(fetchUnenrolledStudents.rejected, (state, action) => {
        state.loadingUnenrolled = false;
        state.errorUnenrolled = action.payload || action.error.message;
      });
  },
});

export default analyticsSlice.reducer;
