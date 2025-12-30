import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import apiList from "../../api.json"
import api from "../utility/api"

const API_URL = import.meta.env.VITE_API_BASE_URL;

export const fetchStudents = createAsyncThunk("students/fetchStudents",

    async (_, { rejectWithValue, getState }) => {
        try {
            const { auth } = getState()
            const token = auth?.token || localStorage.getItem("access");

            // console.log("token", token)
            // console.log("Token in localStorage:", localStorage.getItem("access"))

            const response = await api.get(`${API_URL}${apiList.student.studentList}`, {
                headers: { Authorization: `Bearer ${token}` },
            });

            // console.log("API response:", response.data);

            return response.data;
        } catch (err) {
            return rejectWithValue(err.response?.data || err.message);
        }
    }
);

const studentSlice = createSlice({
    name: "students",
    initialState: {
        list: [],
        loading: false,
        error: null
    },
    reducers: {},
    extraReducers: builder => {
        builder
            .addCase(fetchStudents.pending, state => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchStudents.fulfilled, (state, action) => {
                state.loading = false;
                // state.list = action.payload;
                // state.list = Array.isArray(action.payload)
                //     ? action.payload
                //     : action.payload?.data || [];
                if (Array.isArray(action.payload)) {
                    state.list = action.payload;
                } else if (Array.isArray(action.payload?.data)) {
                    state.list = action.payload.data;
                } else {
                    state.list = [];
                }
            })
            .addCase(fetchStudents.rejected, (state, action) => {
                state.loading = false;
                state.error = action.error.message || action.error.message || "Something went wrong";
                state.list = [];
            });
    }
});

export default studentSlice.reducer;