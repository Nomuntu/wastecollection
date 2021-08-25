const driverNameInput = $('#driver-name')
const driverUsernameInput = $('#username')
const driverPhoneInput = $('#phone')
driverNameInput.on('input', _ => clearValidityIndicators(driverNameInput))
driverUsernameInput.on('input', _ => clearValidityIndicators(driverUsernameInput))
driverPhoneInput.on('input',_ => clearValidityIndicators(driverPhoneInput))

$(':input').keydown(callOnEnter(submitDriverCreationForm))
$('#submit').click(submitDriverCreationForm)

function submitDriverCreationForm() {
    const phone = driverPhoneInput.val()
    if (validateNotEmpty(driverNameInput) && validateNotEmpty(driverUsernameInput) && validatePhoneNumber(phone, driverPhoneInput)) {
        fetch(location.href, {
                method: 'POST',
                headers: {
                        "Content-Type": "application/json"
                },
                body: JSON.stringify({name: driverNameInput.val(), username: driverUsernameInput.val(), phone: phone })
            }
        ).then(resp => {
            if (resp.ok){
                return resp.text();
            } else if (resp.status === 409) {
                $('#username-invalid-feedback').html("Username is taken, please choose another one")
                driverUsernameInput.addClass('is-invalid')
            }
        }).then(body => {
            document.open()
            document.write(body)
            document.close()

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