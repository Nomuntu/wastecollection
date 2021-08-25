const bagSizeDropdown = $('#bag-size')
const materialDropdown = $('#material')
const numBagsInput = $('#num-bags')

const wasteEntryInputs = [bagSizeDropdown, materialDropdown, numBagsInput]

// unbind previous call on enter bindings
// the order in which files are included matters
wasteEntryInputs.forEach(input => input.unbind())
wasteEntryInputs.forEach(input => input.keydown(callOnEnter(addBags)))

bagSizeDropdown.change(_ => clearValidityIndicators(bagSizeDropdown))
materialDropdown.change(_ => clearValidityIndicators(materialDropdown))
numBagsInput.change(_ => clearValidityIndicators(numBagsInput))

$('#add-bag-btn').click(addBags)

function addRow() {
    const bagSize = $('#bag-size option:selected')
    const material = $('#material option:selected')
    const numBags = numBagsInput.val()
    const rowId = nextRowId++
    waste[rowId] = {bag_size: bagSize.val(), material: material.val(), num_bags: numBags}

    createRow(rowId, bagSize.val(), material.val(), numBags)
    $('#bag-info-table-placeholder').hide()
    $('#bag-info-table').show()
}

function deleteRow(rowId) {
    $(`#row_${rowId}`).remove()
    delete waste[rowId]
}
