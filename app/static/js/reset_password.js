const newPasswordInput = $('#password')
const newPasswordRepeatInput = $('#password-repeat')
newPasswordInput.on('input', _ => clearValidityIndicators(newPasswordInput))
newPasswordRepeatInput.on('input', _ => clearValidityIndicators(newPasswordRepeatInput))

$(':input').keydown(callOnEnter(submitPasswordResetForm))
$('#reset-submit').click(submitPasswordResetForm)

function submitPasswordResetForm() {
    if (validateNotEmpty(newPasswordInput) && validateRepeatCorrect(newPasswordInput.val(), newPasswordRepeatInput)) {
        fetch(location.href, {
                method: 'POST',
                headers: {
                        "Content-Type": "application/json"
                },
                body: JSON.stringify({new_password: newPasswordInput.val()})
            }
        ).then(resp => {
            if (resp.ok) {
                resp.text().then(body=>location.href=body)
            }
        })
    }
}

function validateRepeatCorrect(match, repeatDiv){
    clearValidityIndicators(repeatDiv)

    if (repeatDiv.val() !== match) {
        repeatDiv.addClass('is-invalid')
        return false
    } else {
        repeatDiv.addClass('is-valid')
        return true
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