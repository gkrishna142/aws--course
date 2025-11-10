// src/redux/courseSlice.js
import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import apiList from "../../api.json"; 
import api from "../utility/api";

const API_URL = import.meta.env.VITE_API_BASE_URL;

// Thunk: fetch courses
export const fetchCourses = createAsyncThunk(
  "courses/fetchCourses",
  async (_, { rejectWithValue, getState }) => {
    try {
      const { auth } = getState(); // get token if needed
      const token = auth?.token || localStorage.getItem("access");

      const response = await api.get(
        `${API_URL}${apiList.courses.coursesList}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

    if (Array.isArray(response.data?.data)) return response.data;
      

      return [];
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

const courseSlice = createSlice({
  name: "courses",
  initialState: {
    list: [],
    loading: false,
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchCourses.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchCourses.fulfilled, (state, action) => {
        state.loading = false;
        state.list = action.payload?.data || [];
      })
      .addCase(fetchCourses.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || action.error?.message;
      });
  },
});

export default courseSlice.reducer;