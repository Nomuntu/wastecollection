$(':input').keydown(callOnEnter(submitVerification))

$('#verification-submit').on('click', submitVerification)

function submitVerification() {
    const entered = $('#code-entry').val()
    console.log(entered)

    fetch('/collector_verification', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({smsCode: entered})
    }).then(res => res.json())
      .then(res => {
        // === bool because I am unsure about equality in javascript with non bool args
        if (res['expired'] === true) {
            alert('Your sms code has expired. You are being redirected to login')
        } else if (res['code_correct'] === false) {
            alert('This is not the correct code')
        }

        location.href = res['url']
    })
}
