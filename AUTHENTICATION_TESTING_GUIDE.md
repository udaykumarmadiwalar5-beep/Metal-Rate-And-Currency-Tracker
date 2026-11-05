# 🧪 Quick Authentication Testing Guide

## ⚡ Quick Start Testing

### Step 1: Verify Server is Running
Visit: `http://127.0.0.1:5001/` and confirm you see a page

### Step 2: Test Registration Page
**URL:** `http://127.0.0.1:5001/register`

#### Test Case 1: Invalid Username (too short)
- Username: `ab` → Should show: "⚠️ Username must be at least 3 characters"
- Result: ✅ Should REJECT

#### Test Case 2: Valid Email Formats
Try these emails (all should be ACCEPTED):
- ✅ `user@example.com`
- ✅ `test@company.co.uk`
- ✅ `admin@test.museum`
- ✅ `USER@EXAMPLE.COM` (uppercase)
- ❌ `invalid.email` (should reject)
- ❌ `user@` (should reject)

#### Test Case 3: Password Validation
- Too short: `123` → Should reject "⚠️ Password must be at least 6 characters"
- Valid: `Test@1234` → Should accept
- Mismatch: Password `123456`, Confirm `654321` → Should reject "⚠️ Passwords do not match"

#### Test Case 4: Successful Registration
```
Username: testuser2024
Email: testuser@example.com
Password: SecurePass123
Confirm: SecurePass123
```
**Expected:** Alert "✅ Registration Successful!" → Redirects to Login page

**💡 Note:** If you get network error, confirm:
- Server is running on port 5001 (check URL bar)
- Check browser console (F12) for CORS errors

---

### Step 3: Test Login Page  
**URL:** `http://127.0.0.1:5001/login`

#### Test Case 1: Empty Fields
- Leave Username empty → Should show "Email or username is required." on blur
- Leave Password empty → Should show "Password is required." on blur

#### Test Case 2: Invalid Credentials
```
Username: nonexistent
Password: wrongpassword
```
**Expected:** Toast message "❌ Invalid username/email or password."

#### Test Case 3: Successful Login
```
Username: testuser2024 (or testuser123)
Password: SecurePass123
```
**Expected:** Redirects to dashboard

#### Test Case 4: Email Login
Use registered email instead of username:
```
Email: testuser@example.com
Password: SecurePass123
```
**Expected:** Should work the same as username login

---

### Step 4: Test Forgot/Reset Password
**URL:** `http://127.0.0.1:5001/forgot-password`

#### Test Case 1: Invalid Email
- Email: `invalid.email` → Should reject "Invalid email address."

#### Test Case 2: Non-existent Email
```
Email: nonexistent@example.com
New Password: NewPass123
Confirm: NewPass123
```
**Expected:** Error "❌ No account found for this email"

#### Test Case 3: Password Mismatch
```
Email: testuser@example.com
New Password: NewPass123
Confirm: DifferentPass
```
**Expected:** Error "⚠️ Passwords do not match."

#### Test Case 4: Successful Password Reset
```
Email: testuser@example.com
New Password: UpdatedPass456
Confirm: UpdatedPass456
```
**Expected:** 
1. Success message "✅ Password updated successfully!"
2. 2-second delay
3. Redirect to login page
4. Can login with new password

---

## 🔍 Browser Console Debugging

**How to check for errors:**
1. Open browser (Chrome/Firefox/Edge)
2. Press `F12` to open Developer Tools
3. Click "Console" tab
4. Try registration again
5. Look for error messages in red

**Common error fixes:**
- `Failed to fetch` → Server not running, check port 5001
- `CORS error` → Server headers issue, restart server
- Network error shown in page → Check F12 console for details

---

## 📋 Validation Rules Summary

### ✅ All Validations Now Working

| Page | Field | Min | Max | Format |
|------|-------|-----|-----|--------|
| Register | Username | 3 | 50 | Alphanumeric + underscore |
| Register | Email | - | 100 | user@domain.ext |
| Register | Password | 6 | 100 | Any characters |
| Login | Username/Email | - | 100 | - |
| Login | Password | - | 100 | - |
| Reset | Email | - | 100 | user@domain.ext |
| Reset | New Password | 6 | 100 | Any characters |

---

## 🆘 Troubleshooting

### Issue: "Network error. Please try again."
**Solution:**
- ✅ Fixed! Was caused by wrong port (5000 vs 5001)
- Confirm browser URL shows: `127.0.0.1:5001`
- If still seeing error: Open F12 console and check for CORS errors

### Issue: Email validation says invalid but it looks correct
**Solution:**
- Must contain: `@` and `.`
- Examples that work: `user@example.com`, `test@co.uk`, `admin@test.museum`
- Examples that don't work: `user@`, `@example.com`, `user.example.com`

### Issue: Can't login after registration
**Solution:**
- Confirm you entered the same password during registration
- Remember: Passwords are case-sensitive
- Try "Forgot Password" to reset if needed

---

## 📞 Test Results Template

Use this to document your testing:

```
Date: ___________
Tester: ___________

✅ Register Page
  - Port working: YES / NO
  - Email validation: PASS / FAIL
  - Password validation: PASS / FAIL
  - New account created: YES / NO

✅ Login Page  
  - Can login with username: YES / NO
  - Can login with email: YES / NO
  - Error handling works: YES / NO

✅ Forgot Password Page
  - Email validation: PASS / FAIL
  - Password update: YES / NO
  - Can login with new password: YES / NO

Notes: ___________
```

---

**All pages have been fixed and enhanced!** ✨
