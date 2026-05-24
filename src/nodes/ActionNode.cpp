//
// Created by Xuefeng Huang on 2020/1/30.
//

#include "nodes/ActionNode.h"

#include <utility>
#include <trainable/DiscountedCfrTrainable.h>

ActionNode::ActionNode(vector<GameActions> actions, vector<shared_ptr<GameTreeNode>> childrens, int player,
                       GameTreeNode::GameRound round, double pot, shared_ptr<GameTreeNode> parent) :GameTreeNode(round,pot,std::move(parent)){
    this->actions = std::move(actions);
    this->player = player;
    this->childrens = std::move(childrens);

}

vector<GameActions>& ActionNode::getActions() {
    return this->actions;
}

vector<shared_ptr<GameTreeNode>>& ActionNode::getChildrens() {
    return this->childrens;
}

int ActionNode::getPlayer() {
    return this->player;
}

GameTreeNode::GameTreeNodeType ActionNode::getType() {
    return ACTION;
}

shared_ptr<Trainable> ActionNode::getTrainable(int i,bool create_on_site) {
    if(i > this->trainables.size()){
        throw runtime_error(fmt::format("size unacceptable {} > {} ",i,this->trainables.size()));
    }
    if(this->trainables[i] == nullptr && create_on_site){
        this->trainables[i] = make_shared<DiscountedCfrTrainable>(player_privates,*this);
    }
    return this->trainables[i];
}

void ActionNode::setTrainable(vector<shared_ptr<Trainable>> trainables,vector<PrivateCards>* player_privates) {
    this->trainables = trainables;
    this->player_privates = player_privates;
}

void ActionNode::setActions(const vector<GameActions> &actions) {
    ActionNode::actions = actions;
}

void ActionNode::setChildrens(const vector<shared_ptr<GameTreeNode>> &childrens) {
    ActionNode::childrens = childrens;
}

void ActionNode::lockNode(const map<string,float>& freqs) {
    this->locked_probs.assign(this->actions.size(), 0.0f);
    for (int i = 0; i < (int)this->actions.size(); i++) {
        string key;
        switch (this->actions[i].getAction()) {
            case GameTreeNode::FOLD:  key = "fold";  break;
            case GameTreeNode::CALL:  key = "call";  break;
            case GameTreeNode::RAISE: key = "raise"; break;
            case GameTreeNode::CHECK: key = "check"; break;
            case GameTreeNode::BET:   key = "bet";   break;
            default:                  key = "";      break;
        }
        auto it = freqs.find(key);
        if (it != freqs.end()) this->locked_probs[i] = it->second;
    }
    float total = 0;
    for (float p : this->locked_probs) total += p;
    if (total > 0) {
        for (auto& p : this->locked_probs) p /= total;
    } else {
        fill(this->locked_probs.begin(), this->locked_probs.end(), 1.0f / (float)this->actions.size());
    }
    this->is_locked = true;
}

bool ActionNode::isLocked() const {
    return this->is_locked;
}

const vector<float>& ActionNode::getLockedProbs() const {
    return this->locked_probs;
}

vector<float> ActionNode::getLockedStrategy(int n_hands) const {
    int n_actions = (int)this->locked_probs.size();
    vector<float> strategy(n_actions * n_hands);
    for (int a = 0; a < n_actions; a++)
        for (int h = 0; h < n_hands; h++)
            strategy[a * n_hands + h] = this->locked_probs[a];
    return strategy;
}
