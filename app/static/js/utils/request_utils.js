function addBags() {
    const validBagSize = validateBagSize()
    const validMaterial = validateMaterial()
    const validNumBags = validateNumBags()

    $('#empty-request-invalid-feedback').hide()

    if (validBagSize && validMaterial && validNumBags) {
        addRow()
    } else {
        $('#invalid-request-invalid-feedback').show()
    }
}

function validateBagSize() {
    const invalidBagSize = $('#bag-size option:selected').prop('disabled')
    clearValidityIndicators(bagSizeDropdown)

    if (invalidBagSize) {
        bagSizeDropdown.addClass('is-invalid')
    } else {
        bagSizeDropdown.addClass('is-valid')
    }

    return !invalidBagSize
}

function validateMaterial() {
    const invalidWasteType = $('#material option:selected').prop('disabled')
    clearValidityIndicators(materialDropdown)

    if (invalidWasteType) {
        materialDropdown.addClass('is-invalid')
    } else {
        materialDropdown.addClass('is-valid')
    }

    return !invalidWasteType
}

function validateNumBags() {
    const numBags = numBagsInput.val()
    const invalidNumBags = numBags.length === 0 || numBags < 1
    clearValidityIndicators(numBagsInput)

    if (invalidNumBags) {
        numBagsInput.addClass('is-invalid')
    } else {
        numBagsInput.addClass('is-valid')
    }

    return !invalidNumBags
}

