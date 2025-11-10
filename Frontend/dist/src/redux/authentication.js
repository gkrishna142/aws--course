import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';
import apiList from '../../api.json'
import api from "../utility/api"
 
const API_URL = import.meta.env.VITE_API_BASE_URL;

 
export const loginUser = createAsyncThunk(
  'auth/loginUser',
  async (credentials, { rejectWithValue }) => {

    try {
      const response = await api.post(API_URL + apiList.auth.login, credentials);
      return response.data;
 
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);
 
export const getProfile = createAsyncThunk(
  'auth/getProfile',
  async (_, { rejectWithValue, getState }) => {
    console.log("click")
    try {
      const token = getState().auth.token;
      const response = await api.get(API_URL + apiList.auth.getProfile, {
        headers: { Authorization: `Bearer ${token}` },
      });
      return response.data;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);
// logout API
export const logoutUser = createAsyncThunk(
  'auth/logoutUser',
  async (_, { rejectWithValue, getState }) => {
    try {
      const { auth } = getState();
      const refreshToken = auth.refreshToken;
      const accessToken = auth.token;
 
      const response = await api.post(
        apiList.auth.logout,
        { refresh: refreshToken },
        {
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${accessToken}`,
          },
        }
      );
 
      return response.data;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

// refresh token api
export const refreshTokenThunk = createAsyncThunk(
  'auth/refreshToken',
  async (_, { rejectWithValue, getState }) => {
    try {
      const { auth } = getState();
      const refreshToken = auth.refreshToken;
 
      if (!refreshToken) {
        return rejectWithValue('No refresh token found');
      }
 
      const response = await axios.post(
        `${API_URL}${apiList.auth.refreshToken}`,
        { refresh: refreshToken },
        { headers: { 'Content-Type': 'application/json' } }
      );
 
      return response.data;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);
 
 

const authSlice = createSlice({
  name: 'auth',
  initialState: {
  user: JSON.parse(localStorage.getItem('userData')) || null,
  token: localStorage.getItem('access') || null,
  refreshToken: localStorage.getItem('refresh') || null,
  loading: false,
  error: null,
  success: false,
},
  reducers: {
    logout: (state) => {
      state.user = null;
      state.token = null;
      state.refreshToken = null;
      localStorage.removeItem('access');
      localStorage.removeItem('refresh');
      localStorage.removeItem('userData');
    },
  },
  extraReducers: (builder) => {
        // Login
    builder.addCase(loginUser.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(loginUser.fulfilled, (state, action) => {
      // console.log("Login successful:", action.payload);

      
      state.loading = false;
      state.success = true;
      state.error = null;
 
      // ✅ Save tokens properly
      state.token = action.payload.data.access;
      state.refreshToken = action.payload.data.refresh;
 
      state.user = {
        user_type: action.payload.data.user_type,
        is_trial: action.payload.data.is_trial,
        has_purchased: action.payload.data.has_purchased,
        trial_ends_at: action.payload.data?.trial_ends_at,
        trial_remaining_seconds: action.payload.data?.trial_remaining_seconds,
      };
 
      // ✅ Store in localStorage
      localStorage.setItem('access', action.payload.data.access);
      localStorage.setItem('refresh', action.payload.data.refresh);
      localStorage.setItem('userData', JSON.stringify(state.user));
    });
 
    builder.addCase(loginUser.rejected, (state, action) => {
      state.loading = false;
      state.success = false;
      state.error = action.payload;
    });
 
    // Profile
    builder.addCase(getProfile.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(getProfile.fulfilled, (state, action) => {
      state.loading = false;
      state.user = action.payload.data;
      localStorage.setItem("userData", JSON.stringify(action.payload.data));
    });
    builder.addCase(getProfile.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload;
    });
 

    // log out
     builder.addCase(logoutUser.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(logoutUser.fulfilled, (state) => {
      state.loading = false;
      state.user = null;
      state.token = null;
      state.refreshToken = null;
 
      localStorage.removeItem('access');
      localStorage.removeItem('refresh');
      localStorage.removeItem('userData');
    });
    builder.addCase(logoutUser.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload;
      localStorage.removeItem('access');
      localStorage.removeItem('refresh');
      localStorage.removeItem('userData');
    });
  },
 
});
 
export const { logout } = authSlice.actions;
export default authSlice.reducer;
 
 