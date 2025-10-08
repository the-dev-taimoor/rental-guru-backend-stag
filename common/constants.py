email_templates = {
    'SIGNUP': {
        'subject': 'Rental Guru – Verify Your Email Address',
        'html_message': """
                        <html>
                        <body>
                            <p>Hi {USER_FIRST_NAME},</p>
                            <p>Thank you for signing up with Rental Guru!</p>
                            <p>To complete your registration, please verify your email address by entering the following One-Time Password (OTP) in the required field:</p>
                            <h3 style="font-size: 24px; color: #1a73e8;">{OTP_CODE}</h3>
                            <p>This OTP is valid for 1 minute. Please do not share it with anyone.</p>
                            <p>If you didn’t sign up, please ignore this email or contact us at <a href="mailto:support@rentalguru.app">support@rentalguru.app</a>.</p>
                            <br>
                            <p>Warm regards,</p>
                            <p>Rental Guru Team</p>
                        </body>
                        </html>
                        """,
        'duration': 1
    },
    'FORGOT-PASSWORD': {
        'subject': 'Rental Guru – Password Reset Request',
        'html_message': """
                        <html>
                        <body>
                            <p>Hi {USER_FIRST_NAME},</p>
                            <p>We received a request to reset the password for your Rental Guru account.</p>
                            <p>To proceed, please use the following One-Time Password (OTP):</p>
                            <h3 style="font-size: 24px; color: #1a73e8;">{OTP_CODE}</h3>
                            <p>This OTP is valid for 1 minute. Please do not share it with anyone.</p>
                            <p>If you have any questions or need assistance, please reach out at <a href="mailto:support@rentalguru.app">support@rentalguru.app</a>.</p>
                            <br>
                            <p>Thank you for using Rental Guru!</p>
                            <p>Best Regards,</p>
                            <p>Rental Guru Team</p>
                        </body>
                        </html>
                        """,
        'duration': 1
    },
    'SEND-OTP': {
        'subject': 'Rental Guru – Verify your account',
        'html_message': """
                        <html>
                        <body>
                            <p>Hi {USER_FIRST_NAME},</p>
                            <p>We received a request for otp for your Rental Guru account.</p>
                            <p>To proceed, please use the following One-Time Password (OTP):</p>
                            <h3 style="font-size: 24px; color: #1a73e8;">{OTP_CODE}</h3>
                            <p>This OTP is valid for 1 minute. Please do not share it with anyone.</p>
                            <p>If you have any questions or need assistance, please reach out at <a href="mailto:support@rentalguru.app">support@rentalguru.app</a>.</p>
                            <br>
                            <p>Thank you for using Rental Guru!</p>
                            <p>Best Regards,</p>
                            <p>Rental Guru Team</p>
                        </body>
                        </html>
                        """,
        'duration': 1
    },
    'INVITE-OWNER': {
        'subject': 'Action Required: Complete Your Property Co-Ownership Details',
        'html_message': """
                        <html>
                          <body>
                            <p>Hi there,</p>
                            <p>You've been added as a co-owner for a property on our platform.</p>
                            <p>To get started:</p>
                            <ol>
                              <li>Set up your password using the link below.</li>
                              <li>Complete your KYC verification to unlock all platform features.</li>
                            </ol>
                            <p>Once verified, you’ll receive a confirmation email of being added as a Property Owner to their portfolio.</p>
                            <p>
                              <a href="{SETUP_LINK}" style="display:inline-block; padding:10px 20px; background-color:#1a73e8; color:#ffffff; text-decoration:none; border-radius:4px;">
                                Set Up Your Account
                              </a>
                            </p>
                            <p>If you have any questions or need help, feel free to contact our support team at <a href="mailto:support@rentalguru.app">support@rentalguru.app</a>.</p>
                            <br>
                            <p>Thank you!</p>
                            <p>Best Regards,</p>
                            <p>Rental Guru Team</p>
                          </body>
                        </html>
                        """
    },
    'INVITE-EXISTING-OWNER': {
        'subject': 'Action Required: Complete Your Property Co-Ownership Details',
        'html_message': """
                        <html>
                          <body>
                            <p>Hi there,</p>
                            <p>You've been added as a co-owner for a property on our platform.</p>
                            <p>To get started:</p>
                            <ol>
                              <li>Log in to your existing account.</li>
                              <li>Complete your KYC verification to unlock all platform features.</li>
                            </ol>
                            <p>Once verified, you’ll receive a confirmation email of being added as a Property Owner to their portfolio.</p>
                            <p>If you have any questions or need help, feel free to contact our support team at <a href="mailto:support@rentalguru.app">support@rentalguru.app</a>.</p>
                            <br>
                            <p>Thank you!</p>
                            <p>Best Regards,</p>
                            <p>Rental Guru Team</p>
                          </body>
                        </html>
                        """
    },
    'INVITE-VENDOR': {
        'subject': 'Invitation to Join Rental Guru as a Trusted Vendor',
        'html_message': """
                        <html>
                          <body>
                            <p>Hi {VENDOR_FIRST_NAME} {VENDOR_LAST_NAME},</p>
                            <p>You've been invited to join Rental Guru as a vendor.</p>
                            <p>Please complete your profile and start offering your services.</p>
                            <p>
                              <a href="{SETUP_LINK}" style="display:inline-block; padding:12px 24px; background-color:#1a73e8; color:#ffffff; text-decoration:none; border-radius:6px; font-weight:bold;">
                                Complete Your Profile
                              </a>
                            </p>
                            <p>Best Regards,</p>
                            <p>Rental Guru Team</p>
                          </body>
                        </html>
                        """
    },
    'INVITE-TENANT': {
        'subject': 'Invitation to Join Rental Guru as a Tenant',
        'html_message': """
                        <html>
                          <body>
                            <p>Hi {TENANT_FIRST_NAME},</p>
                            <p>You've been invited by {OWNER_NAME} to join Rental Guru as a tenant.</p>
                            <p>Click the button below to create your account and access your lease agreement.</p>
                            <p>
                              <a href="{SETUP_LINK}" style="display:inline-block; padding:12px 24px; text-decoration:none; border-radius:6px; font-weight:bold;">
                                Accept Invitation
                              </a>
                            </p>
                            <p>If you were not expecting this invitation, please ignore this email.</p>
                            <p>— Rental Guru Team</p>
                          </body>
                        </html>
                        """
    },

}


class Success:
    USER_CREATED = "User created successfully! A verification link has been sent to your email."
    OTP_SENT = "OTP has been sent to your email."
    OTP_CODE_VALID = "OTP code is valid."
    TWO_STEP_VERIFICATION_ENABLED = "Two-Step Verification has been enabled successfully."
    TWO_STEP_VERIFICATION_DISABLED = "Two-Step Verification has been disabled successfully."
    VERIFICATION_CODE_SENT = "Verification code sent successfully."
    PASSWORD_UPDATED = "Password updated successfully."
    LOGGED_OUT = "Logged out successfully."
    PROFILE_SETUP = "Profile setup successfully."
    PROFILE_UPDATED = "Profile updated successfully."
    DOCUMENTS_SUBMITTED = "Your documents have been submitted."
    KYC_STATS = "KYC stats."
    KYC_REQUEST_UPDATED_EMAIL_SENT = "KYC request updated and an email response sent."
    KYC_REQUEST_DETAIL = "KYC request detail."
    SERVICE_CATEGORIES = "Service Categories."
    SERVICE_SUBCATEGORIES = "Service Subcategories."
    AMENITIES_AND_SUB_AMENITIES = "Amenities and Sub-amenities."
    AMENITIES_UPDATED = "Property amenities updated successfully."
    PROPERTY_PUBLISHED_STATUS = "Property published status updated successfully"
    UNIT_PUBLISHED_STATUS = "Unit published status updated successfully"
    INVITATION_SENT = "Invitation is sent successfully."
    UNAVAILABILITY_SET = "Unavailable dates added successfully."
    OWNERS_ADDED = "Owners added successfully."
    OWNERS_UPDATED= "Owners detail updated successfully."
    COST_FEE_ADDED = "Cost Fees added successfully."
    COST_FEE_UPDATED = "Cost Fees updated successfully."
    KYC_LIST = "KYC requests list."
    PROPERTIES_LIST = "Properties list."
    UNITS_LIST = "Units list."
    DOCUMENT_DELETED = "Document successfully deleted."
    DOCUMENTS_LIST = "Documents list."
    PROPERTY_METRICS = "Property Metrics."
    COST_FEE_TYPES = "Cost-Fee types."
    ALL_UNITS_CREATED = "All units created successfully."
    LISTING_INFO_UPDATED = "Listing info updated successfully."
    RENTAL_INFO_UPDATED = "Rental details updated successfully."
    UNIT_INFO_UPDATED = "Unit information updated successfully."
    ROLE_ADDED = "Role added successfully."
    VENDOR_INVITATION_SENT = "Vendor invitation sent successfully."
    VENDOR_INVITATIONS_LIST = "Vendor invitations retrieved successfully."
    VENDOR_ROLES_LIST = "Vendor roles retrieved successfully."
    VENDOR_INVITATION_BLOCKED = "Vendor invitation blocked successfully."
    VENDOR_INVITATION_UNBLOCKED = "Vendor invitation unblocked successfully."
    VENDOR_INVITATION_DELETED = "Vendor invitation deleted successfully."
    VENDOR_DETAILS_RETRIEVED = "Vendor details retrieved successfully."
    TENANT_INVITATION_SENT = "Tenant invitation sent successfully."
    TENANT_INVITATIONS_LIST = "Tenant invitations retrieved successfully."
    TENANT_INVITATION_BLOCKED = "Tenant invitation blocked successfully."
    TENANT_INVITATION_UNBLOCKED = "Tenant invitation unblocked successfully."
    TENANT_INVITATION_DELETED = "Tenant invitation deleted successfully."
    TENANT_DETAILS_RETRIEVED = "Tenant details retrieved successfully."
    INVITATION_DETAILS_RETRIEVED = "Invitation details retrieved successfully."
    INVITATION_AGREEMENT_UPDATED = "Invitation agreement updated successfully."
    INVITATION_ACCEPTED = "Invitation accepted successfully."
    INVITATION_REJECTED = "Invitation rejected successfully."
    USER_PROPERTIES_AND_UNITS_LIST = "User properties and units retrieved successfully."
    LEASE_ENDED_SUCCESSFULLY = "Lease ended successfully. Tenant has been blocked and property/unit is now vacant."
    LEASE_RENEWED_SUCCESSFULLY = "Lease renewed successfully. Lease end date has been updated."
    INVITATION_RESENT = "Invitation resent successfully."


class Error:
    USER_NOT_AUTHENTICATED = "Authentication credentials were not provided."
    USER_NOT_FOUND = "User not found."
    OTP_NOT_ENABLED = "OTP is not enabled."
    OTP_CODE_INVALID = "OTP code is invalid."
    OTP_CODE_EXPIRED = "OTP code is expired."
    TOKEN_ERROR_LOGOUT = "Token error during logout."
    ERROR_DURING_LOGOUT = "Error during logout."
    ONLY_SUPER_ADMINS_CAN_VIEW_KYC = "Only super admins can view KYC submissions."
    RESPONSE_VERIFICATION_EMAIL_ERROR = "Error sending verification email."
    RESPONSE_INVITATION_EMAIL_ERROR = "Error sending owner invitation email."
    KYC_RESPONSE_EMAIL_ERROR = "Error while sending kyc response email."
    KYC_STATUS_INVALID = "KYC status should be either approved or rejected."
    ROLE_NOT_ASSIGNED = "Not assigned"
    REFRESH_TOKEN_REQUIRED = "refresh_token is required"
    EMAIL_REQUIRED = "Email is required."
    INVALID_FIELD = "Invalid field."
    OWNER_EXISTS = "This owner is already assigned to this property."
    OWNER_AND_PROPERTY_EXISTS = "This property is already posted from another source."
    PROPERTY_NOT_FOUND = "Property not found."
    UNIT_NOT_FOUND = "Unit not found."
    PUBLISHED_FIELD_REQUIRED = "'published' field is required."
    INVALID_UNIT_TYPE = "Invalid unit type for {}."
    RENT_DETAILS_EXISTS = "Rent details for this property already exist."
    OFFER_NOT_REQUIRED = "Offer is not applicable if tenant is assigned."
    OFFER_REQUIRED = "Offer fields {} are required."
    TENANT_FIELDS_REQUIRED = "{} are required."
    DOCUMENT_TYPE_EXISTS = "A document with this type already exists."
    AVAILABILITY_EXISTS = "Availability selection for {} has already been set."
    UNAVAILABLE_DATES_REQUIRED = "Unavailable dates are required"
    NUMERIC_ZIP_CODE = "Zip code must contain only numeric characters."
    PHOTO_REQUIRED = "At least one photo is required."
    PHOTO_REQUIRED_FOR_UNIT = "Photo required for unit(s): {}"
    COST_FEE_EXISTS = "Cost fee with this name already exists for the specified category."
    COST_FEE_NAME_EXISTS = "Cost fee {} already exists for the specified category."
    EMAIL_ALREADY_ASSIGNED = "{} is already assigned to this property."
    INVITATION_ALREADY_SENT = "Invitation to {} is already sent for this property."
    PAGE_SAVED_REQUIRED = "Page saved is required."
    DOCUMENT_TYPE_EXISTS_V2 = "Document with {} type already exists."
    DOCUMENT_DETAIL_MISSING = "The number of documents must match the number of data objects."
    COST_FEE_ID_MISSING = "Cost-fee id is missing."
    COST_FEE_ID_NOT_FOUND = "Cost-fee with id {} doesnt exist."
    DOC_ID_NOT_FOUND = "Document with id {} doesnt exist."
    DOC_ID_REQUIRED = "Document id is required."
    DATA_REQUIRED = "Document id is required."
    DOCUMENTS_REQUIRED = "Documents are required."
    OWNER_ID_NOT_FOUND = "Owner with id {} doesnt exist."
    DOCUMENT_NOT_FOUND = "Document not found."
    DOCUMENT_DELETE_PERMISSION = "You do not have permission to delete this document."
    PROPERTY_ID_REQUIRED = "Property ID is required in query params."
    NO_CSV_FILE_UPLOADED = "No CSV file uploaded."
    UNSUPPORTED_FILE_FORMAT = "No CSV file uploaded."
    SOME_UNITS_NOT_CREATED = "{} unit(s) created successfully and {} unit(s) failed"
    NUMBER_OF_UNITS_MISMATCH = "Unit limit exceeded: Maximum {} units allowed (currently {} added). Your file contains {} units."
    LISTING_INFO_NOT_FOUND = "Listing for this property doesnt exist."
    RENTAL_DETAIL_NOT_FOUND = "Rental Detail for this {} doesnt exist."
    ROLE_ALREADY_ASSIGNED = "{} role is already assigned."
    DESKS_REQUIRED = "Desks are required for university housing."
    BEDS_REQUIRED = "Beds are required for university housing."
    BEDROOMS_REQUIRED = "Bedrooms are required."
    BATHROOMS_REQUIRED = "Bathrooms are required."
    RENTAL_TYPE_UNIVERSITY_HOUSING = "Rental type should be monthly billing or semester billing for university housing."
    OTHERS_RENTAL_TYPE = "Rental type should be short term or long term for this property type."
    SEMESTER_REQUIRED = "Semester is required for semester billing."
    INVALID_PAYMENT_FREQUENCY_UNIVERSITY_HOUSING = "Payment frequency should be one time, monthly, quarterly or yearly for university housing."
    INVALID_PAYMENT_FREQUENCY_OTHERS = "Payment frequency should be one time, monthly or per use for this property type."
    DOCUMENT_TYPE_UNIVERSITY_HOUSING = "Please select correct document type for university housing."
    DOCUMENT_TYPE_OTHERS = "Please select correct document type for {}."
    UNIT_NOT_OWNED = "You don't have permission to access this unit."
    VENDOR_INVITATION_ALREADY_SENT = "Invitation already sent to {} for {} role."
    VENDOR_INVITATION_ALREADY_ACCEPTED = "Invitation already accepted by {} for {} role."
    INVALID_VENDOR_ROLE = "Invalid vendor role: {}. Valid roles are: {}"
    VENDOR_INVITATION_SEND_FAILED = "Failed to send vendor invitation: {}"
    VENDOR_INVITATION_NOT_FOUND = "Vendor invitation not found."
    VENDOR_INVITATION_DELETE_FAILED = "Failed to delete vendor invitation: {}"
    VENDOR_INVITATION_BLOCK_FAILED = "Failed to block vendor invitation: {}"
    INVITATION_ID_REQUIRED = "invitation_id is required"
    BLOCKED_FIELD_REQUIRED = "blocked field is required"
    VENDOR_NOT_FOUND_FOR_INVITATION = "No vendor found for this invitation."
    VENDOR_INVITATION_NOT_ACCEPTED = "Vendor invitation has not been accepted yet."
    VENDOR_ALREADY_EXISTS = "A vendor with this email already exists."
    VENDOR_ALREADY_EXISTS_V2 = "A vendor with {} email already exists."
    INVITATION_SENT_TO_EMAIL = "Invitation sent to {}"
    TENANT_PROFILE_ALREADY_EXISTS = "A tenant profile for this user already exists."
    PROPERTY_OWNER_PROFILE_ALREADY_EXISTS = "A property owner profile for this user already exists."
    TENANT_PROFILE_NOT_FOUND = "Tenant profile not found. Please create profile."
    TENANT_INVITATION_ALREADY_SENT = "Invitation already sent to {} for {} tenant type at property '{}'."
    TENANT_INVITATION_ALREADY_ACCEPTED = "Invitation already accepted by {} for {} tenant type at property '{}'."
    INVALID_TENANT_TYPE = "Invalid tenant type: {}. Valid types are: {}"
    TENANT_INVITATION_SEND_FAILED = "Failed to send tenant invitation: {}"
    TENANT_INVITATION_NOT_FOUND = "Tenant invitation not found."
    TENANT_INVITATION_DELETE_FAILED = "Failed to delete tenant invitation: {}"
    TENANT_INVITATION_BLOCK_FAILED = "Failed to block tenant invitation: {}"
    TENANT_NOT_FOUND_FOR_INVITATION = "No tenant found for this invitation."
    TENANT_INVITATION_NOT_ACCEPTED = "Tenant invitation has not been accepted yet."
    INVITATION_NOT_FOUND = "Invitation not found."
    INVALID_INVITATION_TYPE = "Invalid invitation type. Please specify either vendor=true or tenant=true."
    INVITATION_EXPIRED = "This invitation has expired."
    AGREEMENT_MUST_BE_TRUE = "Agreement must be set to true to update the invitation."
    TENANT_ALREADY_EXISTS = "A tenant with this email already exists."
    TENANT_ALREADY_EXISTS_V2 = "A tenant with {} email already exists."
    AGREEMENT_REQUIRED = "You must agree (true) to proceed."
    ACCEPT_FIELD_REQUIRED = "accept field is required."
    INVITATION_TYPE_REQUIRED = "Either vendor=true or tenant=true must be specified."
    INVITATION_ALREADY_ACCEPTED = "This invitation has already been accepted."
    INVITATION_ALREADY_REJECTED = "This invitation has already been rejected."
    PROPERTY_OCCUPIED = "Property is already occupied."
    UNIT_OCCUPIED = "Unit is already occupied."
    LEASE_NOT_ACTIVE = "Lease is not active. Invitation must be accepted to end the lease."
    LEASE_ALREADY_ENDED = "Lease has already been ended for this invitation."
    LEASE_END_FAILED = "Failed to end lease: {}"
    LEASE_RENEWAL_FAILED = "Failed to renew lease: {}"
    ACTION_REQUIRED = "Action field is required. Must be either 'end' or 'renew'."
    INVALID_ACTION = "Invalid action. Must be either 'end' or 'renew'."
    LEASE_END_DATE_REQUIRED = "Lease end date is required for lease renewal."
    INVALID_LEASE_END_DATE = "New lease end date must be after the current lease end date."
    EMAIL_MISMATCH = "Invitation email and user email do not match."
    LEASE_START_DATE_REQUIRED = "Lease start date is required."
    RENT_AMOUNT_REQUIRED = "Rent amount is required."
    LEASE_AGREEMENT_REQUIRED = "Lease agreement is required."
    AGREEMENT_NOT_FOUND = "Agreement not found."
