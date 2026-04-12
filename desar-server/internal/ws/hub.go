package ws

import (
	"encoding/json"
	"log"
	"net/http"
	"sync"
	"time"

	"desar-server/internal/models"

	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool { return true },
}

// Hub gestiona conexiones WS por compañía
type Hub struct {
	mu      sync.RWMutex
	clients map[int64]map[*Client]struct{} // companyID → set of clients
}

type Client struct {
	hub        *Hub
	conn       *websocket.Conn
	companiaID int64
	send       chan []byte
}

var hub = &Hub{clients: make(map[int64]map[*Client]struct{})}

func GetHub() *Hub { return hub }

func (h *Hub) register(c *Client) {
	h.mu.Lock()
	defer h.mu.Unlock()
	if h.clients[c.companiaID] == nil {
		h.clients[c.companiaID] = make(map[*Client]struct{})
	}
	h.clients[c.companiaID][c] = struct{}{}
}

func (h *Hub) unregister(c *Client) {
	h.mu.Lock()
	defer h.mu.Unlock()
	if _, ok := h.clients[c.companiaID][c]; ok {
		delete(h.clients[c.companiaID], c)
		close(c.send)
	}
}

// Broadcast envía un evento a todos los clientes de una compañía
func (h *Hub) Broadcast(companiaID int64, evento *models.WSEvento) {
	data, err := json.Marshal(evento)
	if err != nil {
		return
	}
	h.mu.RLock()
	defer h.mu.RUnlock()
	for c := range h.clients[companiaID] {
		select {
		case c.send <- data:
		default:
			// cliente lento, desconectar
		}
	}
}

// BroadcastAll envía a TODAS las compañías (solo superadmin)
func (h *Hub) BroadcastAll(evento *models.WSEvento) {
	data, _ := json.Marshal(evento)
	h.mu.RLock()
	defer h.mu.RUnlock()
	for _, clients := range h.clients {
		for c := range clients {
			select {
			case c.send <- data:
			default:
			}
		}
	}
}

// ConnectedCount retorna clientes conectados de una compañía
func (h *Hub) ConnectedCount(companiaID int64) int {
	h.mu.RLock()
	defer h.mu.RUnlock()
	return len(h.clients[companiaID])
}

func (c *Client) writePump() {
	ticker := time.NewTicker(30 * time.Second)
	defer func() {
		ticker.Stop()
		c.conn.Close()
	}()
	for {
		select {
		case msg, ok := <-c.send:
			c.conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if !ok {
				c.conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}
			c.conn.WriteMessage(websocket.TextMessage, msg)
		case <-ticker.C:
			c.conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if err := c.conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		}
	}
}

func (c *Client) readPump() {
	defer func() {
		c.hub.unregister(c)
		c.conn.Close()
	}()
	c.conn.SetReadLimit(512)
	c.conn.SetReadDeadline(time.Now().Add(60 * time.Second))
	c.conn.SetPongHandler(func(string) error {
		c.conn.SetReadDeadline(time.Now().Add(60 * time.Second))
		return nil
	})
	for {
		if _, _, err := c.conn.ReadMessage(); err != nil {
			break
		}
	}
}

// Handler HTTP para upgrade a WebSocket
func Handler(w http.ResponseWriter, r *http.Request, companiaID int64) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("[WS] upgrade error: %v", err)
		return
	}
	c := &Client{
		hub:        hub,
		conn:       conn,
		companiaID: companiaID,
		send:       make(chan []byte, 64),
	}
	hub.register(c)
	go c.writePump()
	c.readPump()
}
