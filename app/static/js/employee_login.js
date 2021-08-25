const usernameInput = $('#username')
const passwordInput = $('#password')
usernameInput.on('input', _ => clearValidityIndicators(usernameInput))
passwordInput.on('input', _ => clearValidityIndicators(passwordInput))

$(':input').keydown(callOnEnter(submitLoginForm))
$('#login-submit').click(submitLoginForm)

function submitLoginForm() {
    const credentialsFeedback = $('#invalid-credentials-feedback')
    credentialsFeedback.hide()
    if (validateNotEmpty(usernameInput) && validateNotEmpty(passwordInput)) {
        fetch(location.href, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({username: usernameInput.val(), password: passwordInput.val()})
            }
        ).then(resp => {
            if (resp.ok) {
                console.assert(resp.redirected)
                resp.text().then(body=>location.href=body)
            } else if (resp.status === 403) {
                location.href = '/login'
            } else {
                clearValidityIndicators(usernameInput)
                clearValidityIndicators(passwordInput)
                credentialsFeedback.show()
            }
        })
    }
}

function validateNotEmpty(inputDiv) {
    clearValidityIndicators(inputDiv)

    if (inputDiv.val().length === 0) {
        inputDiv.addClass('is-invalid')
        return false
    } else {
        inputDiv.addClass('is-valid')
        return true
    }
}
