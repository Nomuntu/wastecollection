$('#login-submit').click(submitLoginForm)
$('#name').on('input', _ => clearValidityIndicators($('#name')))
$('#phone-number').on('input', _ => clearValidityIndicators($('#phone-number')))

$(':input').keydown(callOnEnter(submitLoginForm))

function submitLoginForm() {
    const name = $('#name').val()
    const phoneNumber = $('#phone-number').val().replace(/\s+/g, '')
    const nameCorrect = validateName(name, $('#name'))
    const phoneCorrect = validatePhoneNumber(phoneNumber, $('#phone-number'))
    const data = {
        name: name,
        phone: phoneNumber
    }
    if (nameCorrect && phoneCorrect) {
        fetch("/", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            }
        ).then(resp => {
            if (resp.ok) {
                console.assert(resp.redirected)
                resp.text().then(body => location.href = body)
            } else {
                console.error(resp)
                resp.text().then(body => $('html').html(body))
            }
        }).catch(console.error)
    }
}


