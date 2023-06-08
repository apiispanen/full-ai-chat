css = '''
<style>
.chat-message {
    padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex
}
.chat-message.user {
    background-color: #2b313e
}
.chat-message.bot {
    background-color: #475063
}
.chat-message .avatar {
  width: 20%;
}
.chat-message .avatar img {
  max-width: 78px;
  max-height: 78px;
  border-radius: 50%;
  object-fit: cover;
}
.chat-message .message {
  width: 80%;
  padding: 0 1.5rem;
  color: #fff;
}
'''

bot_template = '''
<div class="chat-message bot">
    <div class="avatar">
        <img src="https://i.ibb.co/cN0nmSj/Screenshot-2023-05-28-at-02-37-21.png" style="max-height: 78px; max-width: 78px; border-radius: 50%; object-fit: cover;">
    </div>
    <div class="message">{{MSG}}</div>
</div>
'''

user_template = '''
<div class="chat-message user">
    <div class="avatar">
        <img src="https://i.ibb.co/VggCWzX/bird-4342754-640.jpg">
    </div>    
    <div class="message">{{MSG}}</div>
</div>
'''

chatbot_js = """
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
<script src="https://cdn.socket.io/4.2.0/socket.io.min.js" ></script>

<script>
    var i = 0;
    $(function() {
    var chatWindow = $('#chat-window');
    
    
    var responseDivName = "response-text-".concat(i); 
    chatWindow.append('<div class="bg-gray-300 p-3 rounded-r-lg rounded-bl-lg"><p class="text-sm" id="'+responseDivName +'"></p></div>')

    // Socket IO
    // connect to the server, based on the current URL and add port
    var socket = io.connect('http://localhost:5000');

    socket.on('response', function (data) {

    // var message = data.message;
    // var result_dict = data.result_dict;

    // create a new list item element
    var p = $('<b></b>');
    p.addClass('text-sm');
    p.text(data['message']['content']);
    p.text(data['results_dict']);

    console.log(i);
    console.log("data", data);  // The squads value

    
    // append the list item to the response text
    var responseDivName = "response-text-".concat(i); 

    var responseText = $("#"+responseDivName);
    // make the div style visible
    // console.log(responseText);
    responseText.append(p);

    // Automatically scroll to the bottom of the chat window
    chatWindow.scrollTop(chatWindow[0].scrollHeight);
    responseText.removeClass('hidden');

    // Hide the spinner
    $('#spinner').addClass('hidden');
});

    // to send a message to the server, you can use the 'emit' function
    // this could be tied to a button click or form submission event, for example
    // socket print to console

    socket.emit('message', { prompt: 'Hello, GPT!' });
   
    
    // END socket

    $("#chat-form").on('submit', function(e) {
        i++;

        e.preventDefault();
        var userResponse = $('#prompt').val();
        var chatWindow = $('#chat-window');

        $('#spinner').removeClass('hidden'); // Show the spinner
        var responseDivName = "response-text-".concat(i); 
        console.log(responseDivName);
        chatWindow.append('<div class="flex w-full mt-2 space-x-3 max-w-xs ml-auto justify-end">' +
                        '<div>' +
                            '<div class="bg-blue-600 text-white p-3 rounded-l-lg rounded-br-lg">' +
                                '<p class="text-sm">' + userResponse + '<br>' + '</p>' +
                            '</div>'  +
                        '</div>' +
                        '<div class="flex-shrink-0 h-10 w-10 rounded-full bg-gray-300"></div>' +
                    '</div>');
        chatWindow.scrollTop(chatWindow[0].scrollHeight);
        
         chatWindow.append('<div class="bg-gray-300 p-3 mt-4 hidden rounded-r-lg rounded-bl-lg"  id="'+responseDivName +'"><p class="text-sm"></p></div><span class="just-now text-xs text-gray-500 leading-none">Just now</span>')
         socket.emit('message', { prompt: userResponse });

    });
});

</script>

"""
chatbot_html = """

<div class="text-5xl p-5 text-center">
    <h1>AI Chatbot Test</h1>
</div>
<div class="flex flex-col items-center justify-center w-screen h-[75vh] bg-gray-100 text-gray-800 p-10">
    <!-- Component Start -->
    <div id="reponse-grow" class="flex flex-col flex-grow w-full max-w-xl bg-white shadow-xl rounded-lg overflow-hidden">
        <!-- Chat messages container -->
        <div id="chat-window" class="flex flex-col flex-grow h-0 p-4 overflow-auto">
            <!-- Chat messages will be appended here -->
        </div>

        <!-- Message input form -->
        <div id="spinner" class="w-16 h-16 border-t-4 border-b-4 border-blue-500 rounded-full animate-spin hidden"></div>

        <div class="bg-gray-300 p-4">

            <form id="chat-form" class="flex items-center h-10 w-full rounded px-3 text-sm" method="post" action="/api/ChatGPTWebAPITester">

                <input id="prompt" name="prompt" type="text" placeholder="Type your message…" class="flex-grow outline-none">
                <button type="submit" class="ml-2 bg-blue-600 text-white px-3 py-1 rounded">Send</button>
            </form>
        </div>

        <input type="hidden" id="bot-response" value="{{ response }}">

    </div>
    <!-- Component End  -->
</div>

"""