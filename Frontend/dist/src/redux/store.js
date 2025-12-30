// ** Redux Imports
import rootReducer from './rootReducer'
import { configureStore } from '@reduxjs/toolkit'
import toastMiddleware from "./middleware/toastMiddleware";

const store = configureStore({
  reducer: rootReducer,
  middleware: getDefaultMiddleware => 
    // return getDefaultMiddleware({
    //   serializableCheck: false
    getDefaultMiddleware().concat(toastMiddleware),
//     })
//   }
});

export { store }
