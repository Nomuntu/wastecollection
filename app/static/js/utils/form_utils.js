function clearValidityIndicators(element) {
    element.removeClass('is-invalid')
    element.removeClass('is-valid')
}

function callOnEnter(func) {
    return ev => {
        let enterPressed = false

        // have to check both for portability
        if (ev.key !== undefined) {
            enterPressed = ev.key === 'Enter';
        } else if (ev.keyCode !== undefined) {
            enterPressed = ev.keyCode === 13
        }

        if (enterPressed) {
            func()
        }
    }
}

function validateName(name, nameElemSelector) {
    clearValidityIndicators(nameElemSelector)

    if (name.length === 0) {
        nameElemSelector.addClass('is-invalid')
        return false
    } else {
        nameElemSelector.addClass('is-valid')
        return true
    }
}

function validatePhoneNumber(phoneNumber, phoneElemSelector) {
    const phoneRegex = /^(\+27|27|0)[0-9]{2}( |-)?[0-9]{3}( |-)?[0-9]{4}$/
    const matches = phoneNumber.match(phoneRegex)

    clearValidityIndicators(phoneElemSelector)

    if (matches !== null && matches[0].length === matches.input.length) {
        phoneElemSelector.addClass('is-valid')
        return true
    } else {
        phoneElemSelector.addClass('is-invalid')
        return false
    }
}

