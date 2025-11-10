// redux/paymentSlice.js
import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import apiList from "../../api.json";
import api from "../utility/api"

const API_URL = import.meta.env.VITE_API_BASE_URL;

// Fetch payments from backend
export const fetchPayments = createAsyncThunk(
  "payments/fetch",
  async (_, { rejectWithValue, getState }) => {
    try {
      const { auth } = getState();
      const token = auth?.token || localStorage.getItem("access");

      const response = await api.get(
        `${API_URL}${apiList.payment.paymentList}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      // // Always return an array
      // if (response.data?.results) {
      //   return response.data;
      // }

      // // Some APIs wrap data differently
      // if (Array.isArray(response.data)) {
      //   return response.data;
      // }

       return response.data;

      // return [];
    } catch (err) {
      return rejectWithValue(err.response?.data?.message ||err.response?.data || err.message);
    }
  }
);

const paymentSlice = createSlice({
  name: "payments",
  initialState: {
    list: [],
    loading: false,
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchPayments.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchPayments.fulfilled, (state, action) => {
        state.loading = false;
        
        const payload = action.payload;

        // Normalize possible payload shapes into an array:
        let list = [];

        if (!payload) {
          list = [];
        } else if (Array.isArray(payload)) {
          // API returned an array directly
          list = payload;
        } else if (Array.isArray(payload.data)) {
          // payload.data is array
          list = payload.data;
        } else if (Array.isArray(payload.results)) {
          // payload.results is array
          list = payload.results;
        } else if (Array.isArray(payload.data?.results)) {
          // payload.data.results (pagination)
          list = payload.data.results;
        } else if (Array.isArray(payload.data?.items)) {
          // payload.data.items (other naming)
          list = payload.data.items;
        } else {
          // fallback empty
          list = [];
        }

        state.list = list;
      })
      .addCase(fetchPayments.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || action.error?.message;
      });
  },
});

export default paymentSlice.reducer;
