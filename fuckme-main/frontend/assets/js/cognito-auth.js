// ----------------------------------------------------
// CHANGE THESE THREE VALUES TO MATCH YOUR POOL
const REGION      = "us-east-1";
const USER_POOL_ID = "us-east-1_JibYK00tp";
const CLIENT_ID    = "42ks2kmpdmc2jr76jddghaf35p";
// ----------------------------------------------------

AWS.config.region = REGION;

const poolData = { UserPoolId: USER_POOL_ID, ClientId: CLIENT_ID };
const userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);

/* ------------------------------------------------------------------
   SIGN IN
------------------------------------------------------------------*/
export function signIn({ phone_number, password }, onSuccess, onError) {
  const authDetails = new AmazonCognitoIdentity.AuthenticationDetails({
    Username: phone_number,
    Password: password,
  });

  const cognitoUser = new AmazonCognitoIdentity.CognitoUser({
    Username: phone_number,
    Pool: userPool,
  });

  cognitoUser.authenticateUser(authDetails, {
    onSuccess(session) {
      // Save tokens however you like (localStorage, cookie, etc.)
      localStorage.setItem("idToken",     session.getIdToken().getJwtToken());
      localStorage.setItem("accessToken", session.getAccessToken().getJwtToken());
      localStorage.setItem("refreshToken",session.getRefreshToken().getToken());
      localStorage.setItem("phone_number", phone_number);
      onSuccess(session);
    },
    onFailure: onError,
    newPasswordRequired(userAttrs, requiredAttrs) {
      // Show a prompt for the new password and names on the login page
      let newPasswordDiv = document.getElementById('new-password-div');
      if (!newPasswordDiv) {
        newPasswordDiv = document.createElement('div');
        newPasswordDiv.id = 'new-password-div';
        newPasswordDiv.innerHTML = `
          <div class="bg-white shadow-lg rounded-lg p-6 w-full max-w-md border border-gray-200 mt-6 mb-4">
            <h3 class="text-lg font-semibold text-gray-800 mb-4 flex items-center justify-center"><i class="fas fa-key text-green-500 mr-2"></i>Set New Password</h3>
            <div class="space-y-4">
              <div>
                <label for="given_name" class="block text-gray-700 font-medium mb-1">First Name</label>
                <input id="given_name" name="given_name" type="text" required class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500">
              </div>
              <div>
                <label for="family_name" class="block text-gray-700 font-medium mb-1">Last Name</label>
                <input id="family_name" name="family_name" type="text" required class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500">
              </div>
              <div>
                <label for="new_password" class="block text-gray-700 font-medium mb-1">New Password</label>
                <input id="new_password" name="new_password" type="password" required class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500">
              </div>
              <button id="submitNewPassword" type="button" class="w-full bg-green-500 hover:bg-green-600 text-white font-semibold py-2 rounded-lg transition-colors mt-2 flex items-center justify-center"><i class="fas fa-check mr-2"></i>Set New Password</button>
            </div>
          </div>
        `;
        const form = document.getElementById('loginForm');
        form.appendChild(newPasswordDiv);
      }
      showMessage('You must set a new password and provide your first and last name before signing in.', true);
      document.getElementById('submitNewPassword').onclick = function() {
        const newPassword = document.getElementById('new_password').value;
        const given_name = document.getElementById('given_name').value.trim();
        const family_name = document.getElementById('family_name').value.trim();
        if (!newPassword || newPassword.length < 8) {
          showMessage('New password must be at least 8 characters.', true);
          return;
        }
        if (!given_name || !family_name) {
          showMessage('First and last name are required.', true);
          return;
        }
        cognitoUser.completeNewPasswordChallenge(newPassword, {
          given_name,
          family_name
        }, {
          onSuccess(session) {
            localStorage.setItem("idToken",     session.getIdToken().getJwtToken());
            localStorage.setItem("accessToken", session.getAccessToken().getJwtToken());
            localStorage.setItem("refreshToken",session.getRefreshToken().getToken());
            localStorage.setItem("phone_number", phone_number);
            // Remove the new password UI
            newPasswordDiv.remove();
            onSuccess(session);
          },
          onFailure(err) {
            showMessage(err.message || err, true);
          }
        });
      };
    },
  });
}

/* ------------------------------------------------------------------
   START FORGOT-PASSWORD  (step 1)
------------------------------------------------------------------*/
export function startForgotPassword(phone_number, onSuccess, onError) {
  const cognitoUser = new AmazonCognitoIdentity.CognitoUser({
    Username: phone_number,
    Pool: userPool,
  });

  cognitoUser.forgotPassword({
    onSuccess,
    onFailure: onError,
  });
}

/* ------------------------------------------------------------------
   CONFIRM FORGOT-PASSWORD  (step 2)
------------------------------------------------------------------*/
export function confirmForgotPassword(
  { phone_number, code, newPassword },
  onSuccess,
  onError
) {
  const cognitoUser = new AmazonCognitoIdentity.CognitoUser({
    Username: phone_number,
    Pool: userPool,
  });

  cognitoUser.confirmPassword(code, newPassword, {
    onSuccess,
    onFailure: onError,
  });
}

/* ------------------------------------------------------------------
   SIGN OUT
------------------------------------------------------------------*/
export function signOut() {
  const user = userPool.getCurrentUser();
  if (user) user.signOut();
  localStorage.clear(); 
}

/**
 * Show a message in a #message div above the form. Creates the div if not present.
 * @param {string} msg - The message to display
 * @param {boolean} isError - If true, shows as error (red), else success (green)
 */
export function showMessage(msg, isError = false) {
  let messageDiv = document.getElementById("message");
  if (!messageDiv) {
    // Try to insert above the first form
    const form = document.querySelector("form, #resetForm, #confirmForm");
    if (form && form.parentNode) {
      messageDiv = document.createElement("div");
      messageDiv.id = "message";
      form.parentNode.insertBefore(messageDiv, form);
    } else {
      // Fallback: append to body
      messageDiv = document.createElement("div");
      messageDiv.id = "message";
      document.body.insertBefore(messageDiv, document.body.firstChild);
    }
  }
  messageDiv.textContent = msg;
  messageDiv.style.display = "block";
  messageDiv.className = `mb-4 text-center text-sm font-medium ${isError ? 'text-red-600' : 'text-green-600'}`;
}
