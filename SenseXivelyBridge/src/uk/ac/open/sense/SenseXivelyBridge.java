package uk.ac.open.sense;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;

/*
 * This is the start up class for the Sense-Xively bridging application
 * It uses the Xively4J and HTTPServer libraries to extend a web server that
 * will bridge between Sense's RSS read/write blocks and the xively service
 */
public class SenseXivelyBridge implements HttpHandler{

	public static void main(String[] args) {
		System.out.println("Starting Sense Xively Bridge");
        HttpServer server;
		try {
			server = HttpServer.create(new InetSocketAddress(8080), 0);
	        server.createContext("/xively", new SenseXivelyBridge());
	        server.setExecutor(null); // creates a default executor
	        server.start();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
 	}


	@Override
	public void handle(HttpExchange t) throws IOException {
		StringBuffer rb = new StringBuffer("Response:\n");
		rb.append("URI = " + t.getRequestURI() + "\n");
		rb.append("Method = " + t.getRequestMethod() + "\n");
		rb.append("Input = " + readInputStream(t.getRequestBody()) + "\n");
        t.sendResponseHeaders(200, rb.toString().length());
        OutputStream os = t.getResponseBody();
        os.write(rb.toString().getBytes());
        os.close();
        System.out.println(rb.toString());
		
	}

	/*
	 * Utility method to convert InputStream to string
	 */
	public static String readInputStream (InputStream is) {
	    java.util.Scanner s = new java.util.Scanner(is).useDelimiter("\\A");
	    return s.hasNext() ? s.next() : "";	
	}

	
}
