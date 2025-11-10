import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import apiList from "../../api.json"
import api from "../utility/api"

const API_URL = import.meta.env.VITE_API_BASE_URL;

// Fetch all teachers
export const fetchTeachers = createAsyncThunk(
  "teachers/fetchTeachers",
  async (_, { rejectWithValue, getState }) => {
    try {
      const { auth } = getState()
      const token = auth?.token || localStorage.getItem("access");

      // console.log("token", token)
      // console.log("Token in localStorage:", localStorage.getItem("access"))

      const response = await api.get(`${API_URL}${apiList.teacher.teacherList}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      // console.log("API response:", response.data);

      return response.data;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

export const registerTeacher = createAsyncThunk(
  "teachers/registerTeacher",
  async (teacherData, { rejectWithValue, getState, dispatch }) => {
    try {
      const { auth } = getState();
      const token = auth?.token || localStorage.getItem("access");

      // console.log("Token in registerTeacher:", token);

      const response = await api.post(
        `${API_URL}/api/auth/register/teacher/`,
        teacherData,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // await dispatch(fetchTeachers());
      // return true;

      return response.data;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

const teacherSlice = createSlice({
  name: "teachers",
  initialState: {
    list: [],
    loading: false,
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      // --- Fetch Teachers ---
      .addCase(fetchTeachers.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchTeachers.fulfilled, (state, action) => {
        state.loading = false;
        // console.log("Fetched Teachers:", action.payload);
        state.list = action.payload.data ||[];
      })
      .addCase(fetchTeachers.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message;
      })

      // --- Register Teacher ---
      .addCase(registerTeacher.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(registerTeacher.fulfilled, (state) => {
        state.loading = false;
      })
      .addCase(registerTeacher.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message || action.error?.message ;
      });

  },
});
export default teacherSlice.reducer;
