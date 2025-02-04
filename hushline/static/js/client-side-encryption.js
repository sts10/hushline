function addPadding(value, blockSize = 512) {
  /**
   * To hide what field is being encrypted, we need to pad the value to a (roughly) fixed block size.
   * This function is used to create a padded version of the field by adding random words at the end until it
   * reaches a multiple of 512-character blocks.
   */

  value += "\n\n(Random text generated by Hush Line: lorum ipsum ";

  // Add padding words
  const targetLen = blockSize - (value.length % blockSize);
  let padding = "";
  while (padding.length < targetLen) {
    padding +=
      window.DICEWARE_WORDS[
        Math.floor(Math.random() * window.DICEWARE_WORDS.length)
      ] + " ";
  }
  padding += ")";

  // Return the padded value
  return value + padding;
}

async function encryptMessage(publicKeyArmored, message) {
  if (!publicKeyArmored) {
    console.log(
      "Public key not provided for encryption. Encryption cannot proceed.",
    );
    return false;
  }

  try {
    const publicKey = await openpgp.readKey({ armoredKey: publicKeyArmored });
    const messageText = await openpgp.createMessage({ text: message });
    const encryptedMessage = await openpgp.encrypt({
      message: messageText,
      encryptionKeys: publicKey,
    });
    return encryptedMessage;
  } catch (error) {
    console.error("Error encrypting:", error);
    return false;
  }
}

function loadEmailSettings() {
  const elem = document.getElementById("userEmailSettings");
  if (!elem) {
    console.error("Email settings element not found");
  }
  return JSON.parse(elem.innerHTML);
}

document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("messageForm");
  const encryptedFlag = document.getElementById("clientSideEncrypted");
  const publicKeyArmored = document.getElementById("publicKey")
    ? document.getElementById("publicKey").value
    : "";

  const emailSettings = loadEmailSettings();
  let encryptionSuccessful = true;

  function getFieldValue(field) {
    if (
      field.tagName === "INPUT" ||
      field.tagName === "SELECT" ||
      field.tagName === "TEXTAREA"
    ) {
      return field.value;
    } else if (field.tagName === "UL") {
      const checkedValues = [];
      field
        .querySelectorAll(
          "input[type='checkbox']:checked, input[type='radio']:checked",
        )
        .forEach((input) => {
          checkedValues.push(input.value);
        });
      return checkedValues.join(", ");
    }
  }

  function getFieldLabel(field) {
    return field.getAttribute("data-label");
  }

  form.addEventListener("submit", async function (event) {
    event.preventDefault();

    if (emailSettings.sendEmail) {
      // Build an email body with all fields
      let emailBody = "";
      document.querySelectorAll(".form-field").forEach(async (field) => {
        const value = getFieldValue(field);
        const label = getFieldLabel(field);

        emailBody += `# ${label}\n\n${value}\n\n====================\n\n`;
      });
      const encryptedEmailBody = await encryptMessage(
        publicKeyArmored,
        emailBody,
      );
      if (encryptedEmailBody) {
        const emailBodyEl = document.getElementById("email_body");
        emailBodyEl.value = encryptedEmailBody;
      } else {
        encryptionSuccessful = false;
        console.error("Client-side encryption failed for email body");
      }
    }

    // Loop through all encrypted fields and encrypt them
    document.querySelectorAll(".encrypted-field").forEach(async (field) => {
      const value = getFieldValue(field);
      console.log("Encrypting field:", field, value);

      const paddedValue = addPadding(value);
      const encryptedValue = await encryptMessage(
        publicKeyArmored,
        paddedValue,
      );
      if (encryptedValue) {
        // Replace the field with a hidden field and a disabled textarea (for show) containing the encrypted value
        let fieldName;
        if (field.tagName === "UL") {
          fieldName = field.querySelector("input").name;
        } else {
          fieldName = field.name;
        }

        // Empty out the field
        const fieldContainer = field.parentElement;
        fieldContainer.innerHTML = "";

        // Add a textarea with the encrypted value
        const hiddenInput = document.createElement("input");
        hiddenInput.type = "hidden";
        hiddenInput.name = fieldName;
        hiddenInput.value = encryptedValue;

        const textarea = document.createElement("textarea");
        textarea.disabled = true;
        textarea.value = encryptedValue;

        fieldContainer.appendChild(hiddenInput);
        fieldContainer.appendChild(textarea);
      } else {
        encryptionSuccessful = false;
        console.error("Client-side encryption failed for field:", field.name);
      }
    });

    if (encryptionSuccessful && emailSettings.sendEmail) {
      encryptedFlag.value = "true";
    }

    // Wait for the DOM to update before submitting
    setTimeout(() => {
      form.submit();
    }, 100);
  });
});
